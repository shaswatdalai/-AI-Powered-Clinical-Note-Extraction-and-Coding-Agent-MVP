"""
Agent orchestrator: section -> mask -> extract -> ICD lookup -> verify -> reconcile.

For each note, produces:
- ACCEPTED items (both extractor and verifier agree)
- FLAGGED items (disagreement, low confidence, or unverifiable)
- A trace of every decision

Bounded retries: rejected items get up to 1 re-extraction attempt (deferred).
Escalation: if flagged fraction > 0.4, the whole note is flagged.
"""

from src.masker import mask_pii
from src.extractor import extract
from src.icd_index import icd_lookup
from src.verifier import verify
from src.sectioner import section_note


MAX_ITEMS_PER_NOTE = 50
ESCALATION_THRESHOLD = 0.4


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


def run(note_text: str) -> dict:
    """
    Run the full pipeline on one note.

    Args:
        note_text: raw clinical note text.

    Returns:
        {
            "accepted": [items...],       # verifier said SUPPORTED
            "flagged": [items with reason...],  # rejected or unverifiable
            "trace": [strings...],        # decision log
            "escalated": bool,            # True if flagged fraction > 0.4
        }
    """
    trace: list[str] = []

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
    try:
        extraction = extract(masked)
    except Exception as e:
        trace.append(f"extractor failed: {type(e).__name__}: {str(e)[:80]}")
        return {"accepted": [], "flagged": [], "trace": trace, "escalated": True}

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
        return {"accepted": [], "flagged": [], "trace": trace, "escalated": False}

    if n_items > MAX_ITEMS_PER_NOTE:
        trace.append(f"item count {n_items} > {MAX_ITEMS_PER_NOTE}; escalating note")
        return {"accepted": [], "flagged": [], "trace": trace, "escalated": True}

    # ------------------------------------------------------------------
    # 4. Build verifier items (includes ICD lookups per diagnosis)
    # ------------------------------------------------------------------
    try:
        items = _build_verifier_items(extraction)
    except Exception as e:
        trace.append(f"item building failed: {type(e).__name__}: {str(e)[:80]}")
        return {"accepted": [], "flagged": [], "trace": trace, "escalated": True}

    # ------------------------------------------------------------------
    # 5. Verify
    # ------------------------------------------------------------------
    try:
        verifier_resp = verify(masked, items)
    except Exception as e:
        trace.append(f"verifier failed: {type(e).__name__}; all items flagged")
        return {
            "accepted": [],
            "flagged": [
                {"id": it["id"], "item": it, "reason": "verifier unavailable"}
                for it in items
            ],
            "trace": trace,
            "escalated": True,
        }

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
    # 7. Escalation check
    # ------------------------------------------------------------------
    escalated = False
    if n_items > 0:
        flagged_fraction = len(flagged) / n_items
        if flagged_fraction > ESCALATION_THRESHOLD:
            trace.append(
                f"flagged fraction {flagged_fraction:.2f} > "
                f"{ESCALATION_THRESHOLD}; escalating"
            )
            escalated = True

    # ------------------------------------------------------------------
    # 8. Contradictions and missed items from verifier
    # ------------------------------------------------------------------
    if verifier_resp.contradictions:
        trace.append(f"contradictions: {len(verifier_resp.contradictions)}")
        for c in verifier_resp.contradictions:
            trace.append(f"  contradiction: {c.description}")

    if verifier_resp.missed_items:
        trace.append(f"missed items reported: {len(verifier_resp.missed_items)}")
        for m in verifier_resp.missed_items:
            trace.append(f"  missed [{m.type}]: {m.text}")

    return {
        "accepted": accepted,
        "flagged": flagged,
        "trace": trace,
        "escalated": escalated,
    }