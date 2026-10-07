"""
End-to-end pipeline test: raw note -> mask -> extract -> ICD lookup.

Run from project root:
    python -m src.utils.try_pipeline
"""

from pathlib import Path

from src.extractor import extract
from src.icd_index import icd_lookup, load_index
from src.masker import mask_pii


def main():
    note_path = Path("data/note_001.txt")
    note = note_path.read_text(encoding="utf-8")

    print(f"Note: {note_path} ({len(note)} chars)")

    # 1. Mask PII
    masked, entries = mask_pii(note)
    print(f"Masked {len(entries)} PII items; same length: {len(masked) == len(note)}")

    # 2. Extract
    extraction = extract(masked)
    print(f"Extracted: {len(extraction.diagnoses)} dx, "
          f"{len(extraction.medications)} meds, "
          f"{len(extraction.vitals)} vitals")

    # 3. Load ICD index
    load_index()

    # 4. Look up ICD codes for each diagnosis
    print()
    for dx in extraction.diagnoses:
        result = icd_lookup(dx.normalised_name or dx.name_as_written)
        if isinstance(result, list):
            codes = ", ".join(c["code"] for c in result)
            print(f"  {dx.name_as_written:<30} -> {codes}")
        else:
            print(f"  {dx.name_as_written:<30} -> {result}")


if __name__ == "__main__":
    main()