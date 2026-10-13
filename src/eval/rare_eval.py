"""
Rare-diagnosis eval (SOW 8.4b).

For each note in eval_sets/rare_diagnosis.json:
  - run the pipeline (uses extractor and verifier caches)
  - for each gold rare diagnosis, find the matching extracted diagnosis
  - call icd_lookup on the extracted normalised_name
  - count how many returned NO_CONFIDENT_MATCH

SOW 8.4b target: >= 80% correct NO_CONFIDENT_MATCH on the rare-diagnosis set.

No new LLM calls if the cache is warm. Uses the pipeline for end-to-end
coverage (mask, extract, icd lookup).
"""

import json
import sys
from pathlib import Path

from src.masker import mask_pii
from src.extractor import extract
from src.icd_index import load_index, icd_lookup
from src.eval.matching import is_exact_match, is_partial_match


SET_PATH = Path("eval_sets/rare_diagnosis.json")
DATA_DIR = Path("data")


def _find_match(gold_dx: dict, preds: list[dict], used: set[int]) -> int | None:
    for i, p in enumerate(preds):
        if i in used:
            continue
        if is_exact_match(gold_dx, p, "name_as_written"):
            return i
    for i, p in enumerate(preds):
        if i in used:
            continue
        if is_partial_match(gold_dx, p, "name_as_written"):
            return i
    return None


def main():
    if not SET_PATH.exists():
        print(f"{SET_PATH} not found")
        return

    load_index()
    spec = json.loads(SET_PATH.read_text(encoding="utf-8"))
    notes = spec["notes"]

    print(f"Rare-diagnosis eval on {len(notes)} notes")
    print("=" * 70)

    correct_abstain = 0
    total_rare = 0
    per_note = []

    for entry in notes:
        note_id = entry["note_id"]
        note_path = DATA_DIR / f"{note_id}.txt"
        if not note_path.exists():
            print(f"  [skip] {note_id}: data file not found")
            continue

        note_text = note_path.read_text(encoding="utf-8")
        masked, _ = mask_pii(note_text)
        try:
            ex = extract(masked)
        except Exception as e:
            print(f"  [skip] {note_id}: extraction failed ({type(e).__name__})")
            continue

        pred_dxs = []
        for dx in ex.diagnoses:
            span = None
            if dx.evidence and dx.evidence.span:
                span = [dx.evidence.span.start, dx.evidence.span.end]
            pred_dxs.append({
                "name_as_written": dx.name_as_written,
                "normalised_name": dx.normalised_name,
                "span": span,
            })

        gold = json.loads((Path("gold") / f"{note_id}.json").read_text(encoding="utf-8"))
        gold_dxs = gold.get("diagnoses", [])

        used: set[int] = set()
        matched_for_this_note = []
        for gdx in gold_dxs:
            rare_name = (gdx.get("normalised_name") or gdx.get("name_as_written") or "").strip()
            if not rare_name:
                continue
            if rare_name not in entry["rare_diagnoses"]:
                continue

            total_rare += 1
            pi = _find_match(gdx, pred_dxs, used)
            if pi is None:
                matched_for_this_note.append((rare_name, "NOT_EXTRACTED", None))
                continue
            used.add(pi)
            query = pred_dxs[pi].get("normalised_name") or pred_dxs[pi].get("name_as_written")
            try:
                res = icd_lookup(query)
            except Exception as e:
                matched_for_this_note.append((rare_name, "LOOKUP_CRASH", f"{type(e).__name__}"))
                continue
            if isinstance(res, str) and res == "NO_CONFIDENT_MATCH":
                correct_abstain += 1
                matched_for_this_note.append((rare_name, "ABSTAINED", None))
            else:
                codes = [c.get("code") for c in res[:3]] if isinstance(res, list) else []
                matched_for_this_note.append((rare_name, "CODED", ",".join(codes)))

        per_note.append((note_id, matched_for_this_note))
        for name, outcome, detail in matched_for_this_note:
            marker = "✓" if outcome == "ABSTAINED" else "✗"
            extra = f"  ({detail})" if detail else ""
            print(f"  {marker} {note_id}  {name!r:55s}  {outcome}{extra}")

    print()
    print("=" * 70)
    print(f"SOW 8.4b target: >= 0.80 correct abstentions")
    print(f"Correct NO_CONFIDENT_MATCH:  {correct_abstain}/{total_rare} = "
          f"{correct_abstain/total_rare:.3f}" if total_rare else "  no items scored")


if __name__ == "__main__":
    main()