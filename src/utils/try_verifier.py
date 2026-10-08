"""Run the verifier on the extractor output for note_001."""

from pathlib import Path

from src.extractor import extract
from src.icd_index import icd_lookup, load_index
from src.masker import mask_pii
from src.verifier import verify


def main():
    load_index()
    note = Path("data/note_001.txt").read_text(encoding="utf-8")
    masked, _ = mask_pii(note)

    extraction = extract(masked)

    # Build the item list for the verifier
    items = []
    for i, dx in enumerate(extraction.diagnoses):
        item = {
            "id": f"d{i+1}",
            "type": "diagnosis",
            "text": dx.name_as_written,
            "status": dx.status,
            "span": [dx.evidence.span.start, dx.evidence.span.end] if dx.evidence.span else None,
            "span_text": dx.evidence.quote,
            "icd_candidates": icd_lookup(dx.normalised_name or dx.name_as_written),
        }
        items.append(item)

    for i, med in enumerate(extraction.medications):
        items.append({
            "id": f"m{i+1}",
            "type": "medication",
            "text": med.name,
            "status": med.status,
            "span": [med.evidence.span.start, med.evidence.span.end] if med.evidence.span else None,
            "span_text": med.evidence.quote,
        })

    print(f"Sending {len(items)} items to verifier")
    response = verify(masked, items)
    print(f"\nVerdicts: {len(response.verdicts)}")
    for v in response.verdicts:
        print(f"  {v.id}: {v.verdict} (status_correct={v.status_correct}, icd_fit={v.icd_fit})")
        print(f"      reason: {v.reason}")
    print(f"\nContradictions: {len(response.contradictions)}")
    for c in response.contradictions:
        print(f"  {c.description}")
    print(f"\nMissed items: {len(response.missed_items)}")
    for m in response.missed_items:
        print(f"  [{m.type}] {m.text}")


if __name__ == "__main__":
    main()