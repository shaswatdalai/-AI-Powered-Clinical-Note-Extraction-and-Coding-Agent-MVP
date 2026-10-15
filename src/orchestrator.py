import re
import time
from src.masker import mask_pii
from src.extractor import extract
from src.icd_index import icd_lookup, load_index
from src.verifier import verify
from src.sectioner import section_note
MAX_ITEMS_PER_NOTE = 50
ESCALATION_THRESHOLD = 0.4
_INDEX_LOADED = False
def _ensure_index_loaded() -> None:
    """Load the ICD index once per process, lazily."""
    global _INDEX_LOADED
    if _INDEX_LOADED:
        return
    load_index()
    _INDEX_LOADED = True
def _build_verifier_items(extraction) -> list[dict]:
    """Convert extraction into the shape the verifier expects."""
    items = []
    for i, dx in enumerate(extraction.diagnoses):
        span = None
        if dx.evidence and dx.evidence.span:
            span = [dx.evidence.span.start, dx.evidence.span.end]
        items.append({
            "id": f"d{i+1}",
            "type": "diagnosis",
            "text": dx.name_as_written,
            "status": dx.status,
            "span": span,
            "span_text": dx.evidence.quote if dx.evidence else "",
            "icd_candidates": icd_lookup(dx.normalised_name or dx.name_as_written),
        })
    for i, m in enumerate(extraction.medications):
        span = None
        if m.evidence and m.evidence.span:
            span = [m.evidence.span.start, m.evidence.span.end]
        items.append({
            "id": f"m{i+1}",
            "type": "medication",
            "text": m.name,
            "status": m.status,
            "span": span,
            "span_text": m.evidence.quote if m.evidence else "",
        })
    for i, p in enumerate(extraction.procedures):
        span = None
        if p.evidence and p.evidence.span:
            span = [p.evidence.span.start, p.evidence.span.end]
        items.append({
            "id": f"p{i+1}",
            "type": "procedure",
            "text": p.name,
            "span": span,
            "span_text": p.evidence.quote if p.evidence else "",
        })
    for i, a in enumerate(extraction.allergies):
        span = None
        if a.evidence and a.evidence.span:
            span = [a.evidence.span.start, a.evidence.span.end]
        items.append({
            "id": f"a{i+1}",
            "type": "allergy",
            "text": a.substance,
            "span": span,
            "span_text": a.evidence.quote if a.evidence else "",
        })
    for i, v in enumerate(extraction.vitals):
        span = None
        if v.evidence and v.evidence.span:
            span = [v.evidence.span.start, v.evidence.span.end]
        items.append({
            "id": f"v{i+1}",
            "type": "vital",
            "text": v.name,
            "value": v.value,
            "unit": v.unit,
            "span": span,
            "span_text": v.evidence.quote if v.evidence else "",
        })
    return items
def _normalise_for_substring_match(value: object) -> str:
    """Lowercase text and collapse repeated whitespace for deduplication."""
    return re.sub(r"\s+", " ", str(value or "")).strip().casefold()


def _looks_like_substring_of_existing(missed_text: str, accepted: list[dict]) -> bool:
    """Skip empty missed items or text already contained in accepted text/quotes.

    This cheap guard does not resolve synonyms such as HTN vs hypertension.
    Those require terminology-aware matching and should not be silently removed.
    """
    needle = _normalise_for_substring_match(missed_text)
    if not needle:
        return True

    for accepted_entry in accepted:
        item = accepted_entry.get("item", accepted_entry)
        text = _normalise_for_substring_match(item.get("text", ""))
        span_text = _normalise_for_substring_match(item.get("span_text", ""))
        if needle in f"{text} {span_text}".strip():
            return True
    return False


def _missed_item_to_flag(idx: int, missed) -> dict:
    """Convert a verifier-reported missed item into a flagged entry.
    The shape must match the entries the reviewer UI already knows how
    to render: an `id`, an `item` dict with at least `type` and `text`,
    and a `reason` string.
    IDs are prefixed `missed:` so they never collide with extractor IDs
    (d1, m1, p1, a1, v1, …) and so the frontend can classify the reason
    as "missing" via the existing classifier.
    """
    m_type = getattr(missed, "type", None) or "unknown"
    m_text = getattr(missed, "text", None) or ""
    m_span_text = getattr(missed, "span_text", None) or ""
    return {
        "id": f"missed:{idx}",
        "item": {
            "id": f"missed:{idx}",
            "type": m_type,
            "text": m_text,
            "span_text": m_span_text,
            "span": None,  # the verifier reports text, not offsets
            "source": "verifier-recall-check",
        },
        "reason": (
            "verifier recall check: this item appears in the note but was "
            f"not produced by the extractor (type={m_type}, text={m_text!r})"
        ),
    }
def _summarize_flag_reasons(flagged: list[dict]) -> dict[str, int]:
    """Group flagged entries by a coarse reason category for the trace."""
    counts: dict[str, int] = {}
    for f in flagged:
        rid = str(f.get("id", ""))
        reason = str(f.get("reason", "")).lower()
        if rid.startswith("missed:"):
            cat = "missed_by_extractor"
        elif "status mismatch" in reason:
            cat = "status_mismatch"
        elif "no verdict" in reason:
            cat = "no_verdict"
        elif "unavailable" in reason:
            cat = "verifier_unavailable"
        elif "reject" in reason:
            cat = "verifier_rejected"
        else:
            cat = "other"
        counts[cat] = counts.get(cat, 0) + 1
    return counts
def run(note_text: str) -> dict:
    """
    Run the full pipeline on one note.
    Args:
        note_text: raw clinical note text.
    Returns:
        {
            "accepted": [items...],       # verifier said SUPPORTED
            "flagged": [items with reason...],  # rejected, unverifiable,
                                                # or missed by the extractor
            "trace": [strings...],        # decision log incl. per-stage timing
            "escalated": bool,            # True if flagged fraction > 0.4
            "error": str | None,          # set when the pipeline itself failed
        }
    """
    trace: list[str] = []
    # ------------------------------------------------------------------
    # 0. Ensure the ICD index is loaded (idempotent)
    # ------------------------------------------------------------------
    try:
        _ensure_index_loaded()
    except Exception as e:
        trace.append(f"ICD index load failed: {type(e).__name__}: {str(e)[:120]}")
        return {
            "accepted": [],
            "flagged": [],
            "trace": trace,
            "escalated": False,
            "error": f"icd index load failed: {type(e).__name__}: {str(e)[:200]}",
        }
    # ------------------------------------------------------------------
    # 1. Section
    # ------------------------------------------------------------------
    sections = section_note(note_text)
    trace.append(f"sectioned into {len(sections)} section(s)")
    # ------------------------------------------------------------------
    # 2. Mask
    # ------------------------------------------------------------------
    masked, mask_entries = mask_pii(note_text)
    preserved = len(masked) == len(note_text)
    trace.append(f"masked {len(mask_entries)} PII item(s); length preserved={preserved}")
    # ------------------------------------------------------------------
    # 3. Extract
    # ------------------------------------------------------------------
    t_extract_start = time.perf_counter()
    try:
        extraction = extract(masked)
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)[:200]}"
        trace.append(f"extractor failed: {err}")
        return {
            "accepted": [],
            "flagged": [],
            "trace": trace,
            "escalated": False,
            "error": err,
        }
    extract_seconds = time.perf_counter() - t_extract_start
    trace.append(f"extract took {extract_seconds:.2f}s")
    n_items = (
        len(extraction.diagnoses)
        + len(extraction.medications)
        + len(extraction.procedures)
        + len(extraction.allergies)
        + len(extraction.vitals)
    )
    trace.append(f"extracted {n_items} item(s)")
    if n_items == 0:
        trace.append("no items; nothing to verify")
        return {
            "accepted": [],
            "flagged": [],
            "trace": trace,
            "escalated": False,
            "error": None,
        }
    if n_items > MAX_ITEMS_PER_NOTE:
        trace.append(f"item count {n_items} > {MAX_ITEMS_PER_NOTE}; escalating note")
        return {
            "accepted": [],
            "flagged": [],
            "trace": trace,
            "escalated": True,
            "error": None,
        }
    # ------------------------------------------------------------------
    # 4. Build verifier items (includes ICD lookups per diagnosis)
    # ------------------------------------------------------------------
    try:
        items = _build_verifier_items(extraction)
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)[:200]}"
        trace.append(f"item building failed: {err}")
        return {
            "accepted": [],
            "flagged": [],
            "trace": trace,
            "escalated": False,
            "error": err,
        }
    # ------------------------------------------------------------------
    # 5. Verify
    # ------------------------------------------------------------------
    t_verify_start = time.perf_counter()
    try:
        verifier_resp = verify(masked, items)
    except Exception as e:
        err = f"{type(e).__name__}: {str(e)[:200]}"
        trace.append(f"verifier failed: {err}; all items flagged")
        return {
            "accepted": [],
            "flagged": [
                {"id": it["id"], "item": it, "reason": "verifier unavailable"}
                for it in items
            ],
            "trace": trace,
            "escalated": False,
            "error": err,
        }
    verify_seconds = time.perf_counter() - t_verify_start
    trace.append(f"verify took {verify_seconds:.2f}s")
    verdicts_by_id = {v.id: v for v in verifier_resp.verdicts}
    # ------------------------------------------------------------------
    # 6. Reconcile
    # ------------------------------------------------------------------
    accepted = []
    flagged = []
    for item in items:
        v = verdicts_by_id.get(item["id"])
        if v is None:
            flagged.append({
                "id": item["id"],
                "item": item,
                "reason": "no verdict returned by verifier",
            })
            continue
        if v.verdict == "SUPPORTED":
            if item["type"] == "diagnosis" and not v.status_correct:
                flagged.append({
                    "id": item["id"],
                    "item": item,
                    "reason": "status mismatch",
                })
                continue
            accepted.append({
                **item,
                "icd_fit": getattr(v, "icd_fit", None),
                "reason": v.reason,
            })
        else:
            flagged.append({
                "id": item["id"],
                "item": item,
                "reason": v.reason or "verifier rejected",
            })
    trace.append(f"verifier: {len(accepted)} accepted, {len(flagged)} flagged")
    # ------------------------------------------------------------------
    # 7. Contradictions and missed items from verifier
    #
    # Trace contract: use ALL-CAPS machine-readable markers only for
    # things the UI needs to react to. Never use natural-language
    # phrases like "missed item" in a trace line — those collide with
    # verifier reasons echoed back into the trace.
    # ------------------------------------------------------------------
    if verifier_resp.contradictions:
        trace.append(f"CONTRADICTIONS_FOUND: {len(verifier_resp.contradictions)}")
        for c in verifier_resp.contradictions:
            trace.append(f"CONTRADICTION_DETAIL: {c.description}")
    promoted_missed_count = 0
    if verifier_resp.missed_items:
        promoted = 0
        skipped = 0
        for idx, m in enumerate(verifier_resp.missed_items):
            missed_text = getattr(m, "text", "") or ""
            if _looks_like_substring_of_existing(missed_text, accepted):
                trace.append(
                    f"MISSED_ITEM_SKIPPED: {missed_text!r} (already present or empty)"
                )
                skipped += 1
                continue
            trace.append(
                f"MISSED_ITEM_DETAIL: type={getattr(m, 'type', 'unknown')} "
                f"text={missed_text!r}"
            )
            # Keep the verifier's original index so IDs remain stable.
            flagged.append(_missed_item_to_flag(idx, m))
            promoted += 1

        # Emit this UI marker once, only when at least one item was promoted.
        promoted_missed_count = promoted
        if promoted > 0:
            trace.append(f"MISSED_ITEMS_PROMOTED: {promoted}")
        if promoted == 0 and skipped > 0:
            trace.append("RECALL_CHECK_OK: all reported items already present")
    else:
        trace.append("RECALL_CHECK_OK: verifier reported no additional items")
    # ------------------------------------------------------------------
    # 8. Escalation check
    # ------------------------------------------------------------------
    escalated = False
    denom = n_items + promoted_missed_count
    if denom > 0:
        flagged_fraction = len(flagged) / denom
        if flagged_fraction > ESCALATION_THRESHOLD:
            trace.append(
                f"FLAGGED_FRACTION_HIGH: {flagged_fraction:.2f} > "
                f"{ESCALATION_THRESHOLD}; escalating"
            )
            escalated = True
    # ------------------------------------------------------------------
    # 9. Compact summary for the trace viewer and for tests
    # ------------------------------------------------------------------
    counts = _summarize_flag_reasons(flagged)
    breakdown = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "none"
    trace.append(f"FLAGGED_BREAKDOWN: {breakdown}")
    trace.append(f"FLAGGED_IDS: {','.join(str(f.get('id', '?')) for f in flagged) or 'none'}")
    return {
        "accepted": accepted,
        "flagged": flagged,
        "trace": trace,
        "escalated": escalated,
        "error": None,
    }