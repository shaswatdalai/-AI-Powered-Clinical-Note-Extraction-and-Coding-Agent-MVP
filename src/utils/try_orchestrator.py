"""Run the orchestrator on note_001."""

from pathlib import Path
from src.icd_index import load_index
from src.orchestrator import run


def main():
    load_index()
    note = Path("data/note_001.txt").read_text(encoding="utf-8")
    result = run(note)

    print(f"Accepted: {len(result['accepted'])}")
    for item in result["accepted"]:
        print(f"  [{item['type']}] {item['text']}")

    print(f"\nFlagged: {len(result['flagged'])}")
    for item in result["flagged"]:
        print(f"  [{item['item']['type']}] {item['item']['text']} -- {item['reason']}")

    print(f"\nEscalated: {result['escalated']}")

    print("\nTrace:")
    for line in result["trace"]:
        print(f"  {line}")


if __name__ == "__main__":
    main()