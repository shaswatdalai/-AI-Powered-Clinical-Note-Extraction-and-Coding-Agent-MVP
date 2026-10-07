"""Run the pipeline on all 12 gold notes and print a comparison."""

import json
import time
from pathlib import Path

from src.extractor import extract
from src.icd_index import icd_lookup, load_index
from src.masker import mask_pii
import sys


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    load_index()
    gold_files = sorted(Path("gold").glob("note_*.json"))[:limit]
    for gold_path in gold_files:
        note_id = gold_path.stem
        note_path = Path("data") / f"{note_id}.txt"
        if not note_path.exists():
            continue

        note = note_path.read_text(encoding="utf-8")
        masked, _ = mask_pii(note)
        extraction = extract(masked)

        gold = json.loads(gold_path.read_text(encoding="utf-8"))

        print(f"\n=== {note_id} ===")
        print(f"  Gold:      {len(gold['diagnoses'])} dx, {len(gold['medications'])} meds")
        print(f"  Extractor: {len(extraction.diagnoses)} dx, {len(extraction.medications)} meds")

        for dx in extraction.diagnoses:
            result = icd_lookup(dx.normalised_name or dx.name_as_written)
            codes = ", ".join(c["code"] for c in result) if isinstance(result, list) else result
            print(f"    {dx.name_as_written:<40} -> {codes}")
            time.sleep(15)   #  Groq free tier requires slow pacing

if __name__ == "__main__":
    main()