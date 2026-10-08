"""
Run the extractor over the gold notes and compute entity-level metrics.

Usage:
    python -m src.eval.run_eval              # process all notes
    python -m src.eval.run_eval 5            # process only the first 5 gold notes
    python -m src.eval.run_eval 5 0.0        # 5 notes, no sleep (cache warm)
    python -m src.eval.run_eval 5 20         # 5 notes, sleep 20s between LLM calls

Notes that are already cached process instantly.
The sleep only kicks in for freshly-processed notes.
"""

import json
import sys
import time
from pathlib import Path

from src.extractor import extract, _cache_key, _read_cache
from src.masker import mask_pii
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


def _extraction_to_dict_list(items: list) -> list[dict]:
    out = []
    for item in items:
        name = (
            getattr(item, "name_as_written", None)
            or getattr(item, "name", None)
            or getattr(item, "substance", None)
            or ""
        )
        span = None
        ev = getattr(item, "evidence", None)
        if ev and ev.span:
            span = [ev.span.start, ev.span.end]
        out.append({
            "name_as_written": name,
            "name": name,
            "substance": name,
            "span": span,
        })
    return out


def _is_cached(masked: str) -> bool:
    """Check whether the extractor response for this masked note is on disk."""
    return _read_cache(_cache_key(masked)) is not None


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    pace = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0

    gold_files = sorted(Path("gold").glob("note_*.json"))
    if limit is not None:
        gold_files = gold_files[:limit]

    print(f"Evaluating on {len(gold_files)} gold notes (pace={pace}s)")

    totals = {et: {"tp": 0, "fp": 0, "fn": 0} for et, _ in ENTITY_TYPES}
    processed = 0
    skipped = 0
    cache_hits = 0

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
            print(f"  [SKIP] {note_id}: extractor failed ({type(e).__name__}: {str(e)[:80]})")
            skipped += 1
            continue

        processed += 1
        if cached_before:
            cache_hits += 1
            print(f"  [cached] {note_id}")
        else:
            print(f"  [fresh]  {note_id}")
            time.sleep(pace)   # only pace on fresh calls

        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        for etype, name_field in ENTITY_TYPES:
            g_list = _gold_to_dict_list(gold.get(etype, []))
            p_list = _extraction_to_dict_list(getattr(extraction, etype, []))
            res = evaluate_entity_type(g_list, p_list, name_field)
            totals[etype]["tp"] += res["tp"]
            totals[etype]["fp"] += res["fp"]
            totals[etype]["fn"] += res["fn"]

    print(f"\nProcessed: {processed} (cached: {cache_hits}, fresh: {processed - cache_hits}), Skipped: {skipped}")
    print("=" * 60)
    print("AGGREGATE METRICS (exact match)")
    print("=" * 60)

    for etype, _ in ENTITY_TYPES:
        t = totals[etype]
        tp, fp, fn = t["tp"], t["fp"], t["fn"]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall) > 0
            else 0.0
        )
        print(f"\n{etype.capitalize()}:")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall:    {recall:.3f}")
        print(f"  F1:        {f1:.3f}")
        print(f"  (tp={tp}, fp={fp}, fn={fn})")


if __name__ == "__main__":
    main()