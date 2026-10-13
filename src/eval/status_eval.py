"""
Measure status correctness for diagnoses and medications.

SOW 8.3 requires >= 90% of accepted medications and diagnoses to carry
the correct status (current vs discontinued; active vs ruled out vs
historical vs suspected).

For each extracted diagnosis and medication, we find the matching gold
item and compare the status fields.

Usage:
    python -m src.eval.status_eval [limit]

No LLM calls. Uses the extractor cache.
"""

import json
import sys
from pathlib import Path

from src.masker import mask_pii
from src.extractor import extract
from src.eval.matching import is_exact_match, is_partial_match


def _dx_to_dict(dx) -> dict:
    span = None
    ev = getattr(dx, "evidence", None)
    if ev is not None and ev.span is not None:
        span = [ev.span.start, ev.span.end]
    return {
        "name_as_written": dx.name_as_written,
        "normalised_name": dx.normalised_name,
        "status": dx.status,
        "span": span,
    }


def _med_to_dict(m) -> dict:
    span = None
    ev = getattr(m, "evidence", None)
    if ev is not None and ev.span is not None:
        span = [ev.span.start, ev.span.end]
    return {
        "name": m.name,
        "status": m.status,
        "span": span,
    }


def _find_match(gold_item: dict, preds: list[dict], used: set[int], name_field: str) -> int | None:
    for i, p in enumerate(preds):
        if i in used:
            continue
        if is_exact_match(gold_item, p, name_field):
            return i
    for i, p in enumerate(preds):
        if i in used:
            continue
        if is_partial_match(gold_item, p, name_field):
            return i
    return None


def _normalize_status(s: str) -> str:
    if not s:
        return ""
    return s.strip().lower().replace(" ", "_").replace("-", "_")


def main():
    args = sys.argv[1:]
    limit = int(args[0]) if args and args[0].isdigit() else None

    gold_files = sorted(Path("gold").glob("note_*.json"))
    if limit:
        gold_files = gold_files[:limit]

    dx_correct = 0
    dx_total = 0
    med_correct = 0
    med_total = 0
    dx_status_confusion: dict[tuple[str, str], int] = {}
    med_status_confusion: dict[tuple[str, str], int] = {}

    for gold_path in gold_files:
        note_id = gold_path.stem
        note_path = Path("data") / f"{note_id}.txt"
        if not note_path.exists():
            continue
        text = note_path.read_text(encoding="utf-8")
        masked, _ = mask_pii(text)
        try:
            ex = extract(masked)
        except Exception as e:
            print(f"  [skip] {note_id}: {e}")
            continue

        gold = json.loads(gold_path.read_text(encoding="utf-8"))

        # diagnoses
        gdxs = gold.get("diagnoses", [])
        pdxs = [_dx_to_dict(d) for d in ex.diagnoses]
        used: set[int] = set()
        for gdx in gdxs:
            pi = _find_match(gdx, pdxs, used, "name_as_written")
            if pi is None:
                continue
            used.add(pi)
            gs = _normalize_status(gdx.get("status", ""))
            ps = _normalize_status(pdxs[pi].get("status", ""))
            dx_total += 1
            if gs == ps:
                dx_correct += 1
            else:
                key = (gs or "(empty)", ps or "(empty)")
                dx_status_confusion[key] = dx_status_confusion.get(key, 0) + 1

        # medications
        gmeds = gold.get("medications", [])
        pmeds = [_med_to_dict(m) for m in ex.medications]
        used = set()
        for gm in gmeds:
            pi = _find_match(gm, pmeds, used, "name")
            if pi is None:
                continue
            used.add(pi)
            gs = _normalize_status(gm.get("status", ""))
            ps = _normalize_status(pmeds[pi].get("status", ""))
            med_total += 1
            if gs == ps:
                med_correct += 1
            else:
                key = (gs or "(empty)", ps or "(empty)")
                med_status_confusion[key] = med_status_confusion.get(key, 0) + 1

    print()
    print("=" * 60)
    print("STATUS CORRECTNESS (SOW 8.3 target: >= 0.90)")
    print("=" * 60)
    if dx_total:
        print(f"  Diagnoses:   {dx_correct}/{dx_total}  = {dx_correct/dx_total:.3f}")
    else:
        print("  Diagnoses:   no matches")
    if med_total:
        print(f"  Medications: {med_correct}/{med_total}  = {med_correct/med_total:.3f}")
    else:
        print("  Medications: no matches")

    if dx_status_confusion:
        print()
        print("  Diagnosis status confusion (gold -> pred, count):")
        for (g, p), n in sorted(dx_status_confusion.items(), key=lambda x: -x[1]):
            print(f"    {g:15s} -> {p:15s}  {n}")
    if med_status_confusion:
        print()
        print("  Medication status confusion (gold -> pred, count):")
        for (g, p), n in sorted(med_status_confusion.items(), key=lambda x: -x[1]):
            print(f"    {g:15s} -> {p:15s}  {n}")


if __name__ == "__main__":
    main()