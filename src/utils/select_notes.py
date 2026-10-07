"""
Select a diverse set of notes from mtsamples.csv for gold labelling.

Picks 12 notes across different specialties, saves each as
data/note_NNN.txt, and prints a summary.

Run from the project root:
    python src/utils/select_notes.py
"""

import json
import pandas as pd
from pathlib import Path


MIN_LENGTH = 200       # skip fragments. notes shorter than this are not included in the sample
SEED = 42              # fixed for reproducibility . 
NUM_NOTES = 12


def main():
    notes = pd.read_csv("data/mtsamples.csv")

    # Clean the data. Note: index is preserved (original CSV row number).
    notes = notes.dropna(subset=["transcription", "medical_specialty"])
    notes = notes[notes["transcription"].str.len() >= MIN_LENGTH]

    # Pick one note per specialty. Uses the original index for tracking.
    sampled = (
        notes.groupby("medical_specialty", group_keys=False)
        .sample(n=1, random_state=SEED)
    )

    # If there are fewer than NUM_NOTES specialties, sample more
    if len(sampled) < NUM_NOTES:
        remaining = notes[~notes.index.isin(sampled.index)]
        extras = remaining.sample(n=NUM_NOTES - len(sampled), random_state=SEED)
        sampled = pd.concat([sampled, extras])

    sampled = sampled.head(NUM_NOTES)

    Path("data").mkdir(exist_ok=True)

    print(f"Selected {len(sampled)} notes:")
    for i, (csv_index, row) in enumerate(sampled.iterrows(), start=1):
        note_id = f"note_{i:03d}"
        text = row["transcription"]
        specialty = row["medical_specialty"]

        # Save note text
        (Path("data") / f"{note_id}.txt").write_text(text, encoding="utf-8")

        # Save metadata sidecar
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

    print(f"\nSaved to data/note_001.txt .. data/note_{len(sampled):03d}.txt")
    print(f"Metadata sidecars: data/note_NNN.meta.json")


if __name__ == "__main__":
    main()