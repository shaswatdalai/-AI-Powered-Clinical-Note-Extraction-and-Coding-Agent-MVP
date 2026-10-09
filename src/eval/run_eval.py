"""
Run the extractor (optionally with verifier) over gold notes.

Usage:
    python -m src.eval.run_eval [limit] [pace] [--verify]

Notes that are cached are processed instantly.
Only fresh notes require LLM calls.
"""

import json
import sys
import time
from pathlib import Path

from src.extractor import extract, _cache_key as _ext_cache_key, _read_cache as _ext_read_cache
from src.masker import mask_pii
from src.verifier import verify
from src.icd_index import icd_lookup, load_index
from src.eval.matching import evaluate_entity_type


ENTITY_TYPES = [
    ("diagnoses", "name_as_written"),
    ("medications", "name"),
    ("procedures", "name"),
    ("allergies", "substance"),
    ("vitals", "name"),
]


def _gold_to_dict_list(raw: list[dict]) -> list[dict]:
    out = []
    for g in raw:
        out.append({
            "name_as_written": g.get("name_as_written") or g.get("name") or g.get("substance") or "",
            "name": g.get("name") or g.get("name_as_written") or g.get("substance") or "",
            "substance": g.get("substance") or "",
            "span": g.get("span"),
        })
    return out


def _entity_to_dict(item, name_field: str) -> dict:
    name = ""
    for field in ("name_as_written", "name", "substance"):
        val = getattr(item, field, None)
        if val:
            name = val
            break
    span = None
    ev = getattr(item, "evidence", None)
    if ev and ev.span:
        span = [ev.span.start, ev.span.end]
    return {
        "name_as_written": name,
        "name": name,
        "substance": name,
        "span": span,
    }


def _is_cached(masked: str) -> bool:
    return _ext_read_cache(_ext_cache_key(masked)) is not None


def _build_verifier_items(extraction) -> list[dict]:
    items = []
    for i, dx in enumerate(extraction.diagnoses):
        span = [dx.evidence.span.start, dx.evidence.span.end] if dx.evidence and dx.evidence.span else None
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
        span = [m.evidence.span.start, m.evidence.span.end] if m.evidence and m.evidence.span else None
        items.append({
            "id": f"m{i+1}", "type": "medication", "text": m.name,
            "status": m.status, "span": span,
            "span_text": m.evidence.quote if m.evidence else "",
        })
    for i, p in enumerate(extraction.procedures):
        span = [p.evidence.span.start, p.evidence.span.end] if p.evidence and p.evidence.span else None
        items.append({
            "id": f"p{i+1}", "type": "procedure", "text": p.name,
            "span": span, "span_text": p.evidence.quote if p.evidence else "",
        })
    for i, a in enumerate(extraction.allergies):
        span = [a.evidence.span.start, a.evidence.span.end] if a.evidence and a.evidence.span else None
        items.append({
            "id": f"a{i+1}", "type": "allergy", "text": a.substance,
            "span": span, "span_text": a.evidence.quote if a.evidence else "",
        })
    for i, v in enumerate(extraction.vitals):
        span = [v.evidence.span.start, v.evidence.span.end] if v.evidence and v.evidence.span else None
        items.append({
            "id": f"v{i+1}", "type": "vital", "text": v.name,
            "value": v.value, "unit": v.unit,
            "span": span, "span_text": v.evidence.quote if v.evidence else "",
        })
    return items


def _filter_by_verdicts(extraction, verdicts_by_id: dict) -> dict:
    out = {"diagnoses": [], "medications": [], "procedures": [], "allergies": [], "vitals": []}

    for i, dx in enumerate(extraction.diagnoses):
        v = verdicts_by_id.get(f"d{i+1}")
        if v and v.verdict == "SUPPORTED" and v.status_correct:
            out["diagnoses"].append(dx)
    for i, m in enumerate(extraction.medications):
        v = verdicts_by_id.get(f"m{i+1}")
        if v and v.verdict == "SUPPORTED" and v.status_correct:
            out["medications"].append(m)
    for i, p in enumerate(extraction.procedures):
        v = verdicts_by_id.get(f"p{i+1}")
        if v and v.verdict == "SUPPORTED":
            out["procedures"].append(p)
    for i, a in enumerate(extraction.allergies):
        v = verdicts_by_id.get(f"a{i+1}")
        if v and v.verdict == "SUPPORTED":
            out["allergies"].append(a)
    for i, vt in enumerate(extraction.vitals):
        v = verdicts_by_id.get(f"v{i+1}")
        if v and v.verdict == "SUPPORTED":
            out["vitals"].append(vt)

    return out


def main():
    args = sys.argv[1:]
    use_verifier = "--verify" in args
    args = [a for a in args if a != "--verify"]

    limit = int(args[0]) if len(args) > 0 else None
    pace = float(args[1]) if len(args) > 1 else 60.0

    if use_verifier:
        print("Loading ICD index...")
        load_index()

    gold_files = sorted(Path("gold").glob("note_*.json"))
    if limit is not None:
        gold_files = gold_files[:limit]

    mode = "VERIFIED" if use_verifier else "RAW"
    print(f"Evaluating on {len(gold_files)} gold notes in {mode} mode (pace={pace}s)")

    totals = {et: {"tp": 0, "fp": 0, "fn": 0} for et, _ in ENTITY_TYPES}
    processed = 0
    fresh = 0
    skipped = 0

    for gold_path in gold_files:
        note_id = gold_path.stem
        note_path = Path("data") / f"{note_id}.txt"
        if not note_path.exists():
            skipped += 1
            continue

        note = note_path.read_text(encoding="utf-8")
        masked, _ = mask_pii(note)

        cached_before = _is_cached(masked)

        try:
            extraction = extract(masked)
        except Exception as e:
            print(f"  [SKIP] {note_id}: extractor failed ({type(e).__name__}: {str(e)[:60]})")
            skipped += 1
            continue

        processed += 1
        if cached_before:
            print(f"  [cached] {note_id}")
        else:
            fresh += 1
            print(f"  [fresh]  {note_id}")
            time.sleep(pace)

        # Apply verifier if requested
        if use_verifier:
            items = _build_verifier_items(extraction)
            if not items:
                extraction_for_eval = {
                    "diagnoses": [], "medications": [], "procedures": [],
                    "allergies": [], "vitals": [],
                }
            else:
                verifier_resp = verify(masked, items)
                verdicts_by_id = {v.id: v for v in verifier_resp.verdicts}
                extraction_for_eval = _filter_by_verdicts(extraction, verdicts_by_id)
        else:
            extraction_for_eval = {
                "diagnoses": extraction.diagnoses,
                "medications": extraction.medications,
                "procedures": extraction.procedures,
                "allergies": extraction.allergies,
                "vitals": extraction.vitals,
            }

        gold = json.loads(gold_path.read_text(encoding="utf-8"))

        for etype, name_field in ENTITY_TYPES:
            g_list = _gold_to_dict_list(gold.get(etype, []))
            p_list = [_entity_to_dict(item, name_field) for item in extraction_for_eval[etype]]
            res = evaluate_entity_type(g_list, p_list, name_field)
            totals[etype]["tp"] += res["tp"]
            totals[etype]["fp"] += res["fp"]
            totals[etype]["fn"] += res["fn"]

    print(f"\nProcessed: {processed} (fresh: {fresh}, cached: {processed - fresh}), Skipped: {skipped}")
    print("=" * 60)
    print(f"AGGREGATE METRICS ({mode}, exact match)")
    print("=" * 60)

    for etype, _ in ENTITY_TYPES:
        t = totals[etype]
        tp, fp, fn = t["tp"], t["fp"], t["fn"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        print(f"\n{etype.capitalize()}:")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall:    {recall:.3f}")
        print(f"  F1:        {f1:.3f}")
        print(f"  (tp={tp}, fp={fp}, fn={fn})")


if __name__ == "__main__":
    main()