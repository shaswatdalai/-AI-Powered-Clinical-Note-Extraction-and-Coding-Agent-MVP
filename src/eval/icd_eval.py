"""
Measure ICD-10 coding accuracy against the gold standard.

For each gold diagnosis that has an icd_code, find the extraction whose
name matches (using the same matcher as the P/R/F1 eval), look up its
ICD candidates, and check whether the gold code appears in the top-1 or
top-3.

Reports:
- top-1 accuracy
- top-3 accuracy
- rate of correct "no confident match" on gold diagnoses (i.e. the
  system returned NO_CONFIDENT_MATCH and the gold code is a rare or
  unmappable one — we treat this as a "maybe correct abstention" only
  when the gold diagnosis has no icd_code)
- coverage: how many gold diagnoses had a matching extraction at all

Usage:
    python -m src.eval.icd_eval [limit]

No LLM calls. Uses the extractor cache.
"""

import json
import sys
from pathlib import Path

from src.masker import mask_pii
from src.extractor import extract
from src.icd_index import load_index, icd_lookup
from src.eval.matching import is_exact_match, is_partial_match


def _extraction_index(extraction) -> list[dict]:
    """Flatten extraction diagnoses into the dict shape the matcher wants."""
    out = []
    for dx in extraction.diagnoses:
        span = None
        ev = getattr(dx, "evidence", None)
        if ev is not None and ev.span is not None:
            span = [ev.span.start, ev.span.end]
        out.append({
            "name_as_written": dx.name_as_written,
            "normalised_name": dx.normalised_name,
            "status": dx.status,
            "span": span,
        })
    return out


def _find_matching_extraction(gold_dx: dict, preds: list[dict], used: set[int]) -> int | None:
    """Return the index of the first unused pred that matches the gold dx."""
    for i, p in enumerate(preds):
        if i in used:
            continue
        if is_exact_match(gold_dx, p, "name_as_written"):
            return i
    # fall back to partial
    for i, p in enumerate(preds):
        if i in used:
            continue
        if is_partial_match(gold_dx, p, "name_as_written"):
            return i
    return None


def _candidate_codes(result) -> list[str]:
    """Extract the code strings from whatever icd_lookup returns."""
    if not result:
        return []
    out = []
    for c in result:
        if isinstance(c, dict):
            code = c.get("code") or c.get("icd_code")
            if code:
                out.append(code)
        else:
            code = getattr(c, "code", None)
            if code:
                out.append(code)
    return out


def main():
    args = sys.argv[1:]
    limit = int(args[0]) if args and args[0].isdigit() else None

    print("Loading ICD index...")
    load_index()

    gold_files = sorted(Path("gold").glob("note_*.json"))
    if limit:
        gold_files = gold_files[:limit]

    top1 = 0
    top3 = 0
    no_confident = 0
    no_match = 0          # gold dx had a code but no extraction matched it
    gold_with_code = 0
    gold_without_code = 0
    correct_abstention = 0  # system said NO_CONFIDENT_MATCH and gold had no code
    total_extractions = 0

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

        preds = _extraction_index(ex)
        total_extractions += len(preds)
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        gold_dxs = gold.get("diagnoses", [])
        used: set[int] = set()

        for gdx in gold_dxs:
            gcode = gdx.get("icd_code")
            if gcode:
                gold_with_code += 1
            else:
                gold_without_code += 1

            pi = _find_matching_extraction(gdx, preds, used)
            if pi is None:
                no_match += 1
                continue
            used.add(pi)

            pred = preds[pi]
            query = pred.get("normalised_name") or pred.get("name_as_written")
            if not query:
                continue
            result = icd_lookup(query)
            codes = _candidate_codes(result)

            if not codes:
                no_confident += 1
                if not gcode:
                    correct_abstention += 1
                continue

            if not gcode:
                # gold has no code; we can't score. skip.
                continue

            if codes[0] == gcode:
                top1 += 1
            if gcode in codes[:3]:
                top3 += 1

    scored = gold_with_code - no_match
    print()
    print("=" * 60)
    print("ICD-10 CODING ACCURACY (gold diagnoses that have icd_code)")
    print("=" * 60)
    print(f"  gold diagnoses with icd_code:   {gold_with_code}")
    print(f"  gold diagnoses without:         {gold_without_code}")
    print(f"  extraction matched a gold dx:   {scored}")
    print(f"  no extraction matched the dx:   {no_match}  (counted as miss)")
    print(f"  system returned NO_CONFIDENT:   {no_confident}  "
          f"(correct abstentions on non-coded gold: {correct_abstention})")
    print()
    if scored > 0:
        print(f"  Top-1 accuracy (of {scored}):  {top1}/{scored}  = {top1/scored:.3f}")
        print(f"  Top-3 accuracy (of {scored}):  {top3}/{scored}  = {top3/scored:.3f}")
    else:
        print("  No scored items.")


if __name__ == "__main__":
    main()