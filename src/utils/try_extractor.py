"""Try the extractor on note_001 and print the result."""
from pathlib import Path
from src.extractor import extract
from src.masker import mask_pii

note = Path("data/note_001.txt").read_text(encoding="utf-8")
masked, entries = mask_pii(note)

print(f"Original length: {len(note)}")
print(f"Masked length:   {len(masked)}")
print(f"Masked items:    {len(entries)}")
print()

extraction = extract(masked)
print(f"Diagnoses:    {len(extraction.diagnoses)}")
print(f"Medications:  {len(extraction.medications)}")
print(f"Procedures:   {len(extraction.procedures)}")
print(f"Allergies:    {len(extraction.allergies)}")
print(f"Vitals:       {len(extraction.vitals)}")
print()

for d in extraction.diagnoses:
    print(f"  DX: {d.name_as_written} ({d.status}) span={d.evidence.span}")