"""Check the masker output on note_001."""

from pathlib import Path
from src.masker import mask_pii, CLINICAL_BLOCKLIST


def main():
    print(f"CLINICAL_BLOCKLIST size: {len(CLINICAL_BLOCKLIST)}")
    note = Path("data/note_001.txt").read_text(encoding="utf-8")
    masked, entries = mask_pii(note)
    print(f"Masked items on note_001: {len(entries)}")
    for e in entries:
        print(f"  [{e['type']}] {e['original']!r}")


if __name__ == "__main__":
    main()