"""
Helper: find character offsets for phrases in a note.

Usage:
    python src/utils/find_spans.py data/note_001.txt "allergic rhinitis" "Flonase"

Prints the start offset, end offset, and the exact slice of text for each phrase.
If a phrase is not found, prints NOT FOUND.
"""

import sys
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print("Usage: python src/utils/find_spans.py <note_path> <phrase1> [<phrase2> ...]")
        sys.exit(1)

    note_path = Path(sys.argv[1])
    phrases = sys.argv[2:]

    note = note_path.read_text(encoding="utf-8")
    print(f"Loaded {note_path} ({len(note)} chars)\n")

    for phrase in phrases:
        start = note.find(phrase)
        if start == -1:
            print(f"{phrase!r}: NOT FOUND")
            continue
        end = start + len(phrase)
        print(f"{phrase!r}:")
        print(f"  start = {start}")
        print(f"  end   = {end}")
        print(f"  slice = {note[start:end]!r}")
        print()


if __name__ == "__main__":
    main()