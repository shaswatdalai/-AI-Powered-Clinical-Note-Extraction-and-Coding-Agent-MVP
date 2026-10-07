"""
Select a diverse set of notes from mtsamples.csv for gold labelling.

Picks notes across different specialties, saves each as
data/note_NNN.txt with a metadata sidecar, and prints a summary.

Notes already selected in previous runs (detected by inspecting
existing .meta.json files) are automatically excluded.

Usage:
    python -m src.utils.select_notes                       # default: 12 notes, note_001..012
    python -m src.utils.select_notes --start 13 --end 27   # 15 notes, note_013..027
    python -m src.utils.select_notes --start 28 --end 40   # 13 notes, note_028..040
"""

import argparse
import json
import pandas as pd
from pathlib import Path


MIN_LENGTH = 200       # skip fragments: notes shorter than this are excluded
SEED = 42              # fixed for reproducibility
DEFAULT_START = 1
DEFAULT_END = 12


def parse_args():
    parser = argparse.ArgumentParser(description="Select clinical notes for gold labelling.")
    parser.add_argument("--start", type=int, default=DEFAULT_START,
                        help=f"First note number (default: {DEFAULT_START})")
    parser.add_argument("--end", type=int, default=DEFAULT_END,
                        help=f"Last note number, inclusive (default: {DEFAULT_END})")
    parser.add_argument("--seed", type=int, default=SEED,
                        help=f"Random seed (default: {SEED})")
    return parser.parse_args()


def load_used_indices() -> set[int]:
    """Return the set of original CSV row indices already used by existing notes."""
    used: set[int] = set()
    for meta_path in Path("data").glob("note_*.meta.json"):
        try:
            data = json.loads(meta_path.read_text(encoding="utf-8"))
            used.add(int(data["original_index"]))
        except Exception:
            # Skip malformed metadata files rather than crash
            continue
    return used


def main():
    args = parse_args()
    start, end = args.start, args.end
    if end < start:
        raise SystemExit(f"--end ({end}) must be >= --start ({start})")

    target_count = end - start + 1
    print(f"Target: {target_count} notes, labelled note_{start:03d} to note_{end:03d}")
    print(f"Seed:   {args.seed}")

    # Load and clean the CSV
    notes = pd.read_csv("data/mtsamples.csv")
    notes = notes.dropna(subset=["transcription", "medical_specialty"])
    notes = notes[notes["transcription"].str.len() >= MIN_LENGTH]
    print(f"CSV: {len(notes)} usable notes after filtering")

    # Exclude notes already used in previous batches
    used = load_used_indices()
    if used:
        before = len(notes)
        notes = notes[~notes.index.isin(used)]
        print(f"Excluded {before - len(notes)} notes already selected in previous batches "
              f"({len(used)} unique indices on record)")

    if len(notes) < target_count:
        raise SystemExit(
            f"Not enough unused notes: need {target_count}, have {len(notes)}"
        )

    # One note per specialty
    sampled = (
        notes.groupby("medical_specialty", group_keys=False)
        .sample(n=1, random_state=args.seed)
    )

    # If we need more than there are specialties, sample extras from remaining rows
    if len(sampled) < target_count:
        remaining = notes[~notes.index.isin(sampled.index)]
        extras = remaining.sample(
            n=target_count - len(sampled),
            random_state=args.seed,
        )
        sampled = pd.concat([sampled, extras])

    # Trim to exactly the target count
    sampled = sampled.head(target_count)

    Path("data").mkdir(exist_ok=True)

    print(f"\nSelected {len(sampled)} notes:")
    for offset, (csv_index, row) in enumerate(sampled.iterrows()):
        note_num = start + offset
        note_id = f"note_{note_num:03d}"
        text = row["transcription"]
        specialty = row["medical_specialty"]

        (Path("data") / f"{note_id}.txt").write_text(text, encoding="utf-8")

        meta = {
            "note_id": note_id,
            "specialty": specialty,
            "original_index": int(csv_index),
            "length": len(text),
        }
        (Path("data") / f"{note_id}.meta.json").write_text(
            json.dumps(meta, indent=2), encoding="utf-8"
        )

        print(f"  {note_id} | {specialty:<35} | {len(text):>5} chars")

    print(f"\nSaved note_{start:03d} through note_{end:03d} in data/")
    print("Metadata sidecars written alongside each note.")


if __name__ == "__main__":
    main()