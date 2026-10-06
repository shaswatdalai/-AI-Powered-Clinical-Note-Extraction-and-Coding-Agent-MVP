"""
Verify that every span in every gold/*.json file slices correctly.

For each item, checks:
    note[start:end] == name_as_written (or equivalent field)

Prints any mismatches. Exit code 0 if all pass, 1 if any fail.
"""

import json
import sys
from pathlib import Path


def check_span(note: str, span: list, expected: str, label: str) -> bool:
    if not isinstance(span, list) or len(span) != 2:
        print(f"  [BAD SPAN] {label}: span is not [start, end]: {span!r}")
        return False
    start, end = span
    actual = note[start:end]
    if actual != expected:
        print(f"  [MISMATCH] {label}")
        print(f"    expected: {expected!r}")
        print(f"    actual:   {actual!r}")
        print(f"    span:     [{start}, {end}]")
        return False
    return True


def main():
    gold_dir = Path("gold")
    all_ok = True

    for gold_file in sorted(gold_dir.glob("note_*.json")):
        note_id = gold_file.stem
        note_path = Path("data") / f"{note_id}.txt"
        if not note_path.exists():
            print(f"[SKIP] {gold_file.name}: no matching note text")
            continue

        note = note_path.read_text(encoding="utf-8")
        data = json.loads(gold_file.read_text(encoding="utf-8"))

        errors = 0

        for dx in data.get("diagnoses", []):
            if not check_span(note, dx.get("span"), dx.get("name_as_written", ""),
                              f"diagnosis {dx.get('name_as_written')!r}"):
                errors += 1

        for med in data.get("medications", []):
            # For medications, the span should cover the drug name at minimum
            # Some notes include the full dose, some just the name.
            # Check that the span text CONTAINS the name (case-insensitive).
            span = med.get("span")
            name = med.get("name", "")
            if not isinstance(span, list) or len(span) != 2:
                print(f"  [BAD SPAN] medication {name!r}: {span!r}")
                errors += 1
                continue
            start, end = span
            actual = note[start:end]
            if name.lower() not in actual.lower():
                print(f"  [MED MISMATCH] {name!r} not in span text {actual!r}")
                print(f"    span: [{start}, {end}]")
                errors += 1

        for proc in data.get("procedures", []):
            span = proc.get("span")
            name = proc.get("name", "")
            if not isinstance(span, list) or len(span) != 2:
                print(f"  [BAD SPAN] procedure {name!r}: {span!r}")
                errors += 1
                continue
            start, end = span
            actual = note[start:end]
            if name.lower() not in actual.lower():
                print(f"  [PROC MISMATCH] {name!r} not in span text {actual!r}")
                errors += 1

        for al in data.get("allergies", []):
            span = al.get("span")
            sub = al.get("substance", "")
            if not isinstance(span, list) or len(span) != 2:
                print(f"  [BAD SPAN] allergy {sub!r}: {span!r}")
                errors += 1
                continue
            start, end = span
            actual = note[start:end]
            if sub.lower() not in actual.lower():
                print(f"  [ALLERGY MISMATCH] {sub!r} not in span text {actual!r}")
                errors += 1

        for v in data.get("vitals", []):
            span = v.get("span")
            if not isinstance(span, list) or len(span) != 2:
                print(f"  [BAD SPAN] vital {v.get('name')!r}: {span!r}")
                errors += 1
                continue
            # vitals: the value should be within the span (may not match exactly
            # if the vital was written with units or slashes)
            start, end = span
            actual = note[start:end]
            value = v.get("value", "")
            if value and value not in actual:
                print(f"  [VITAL MISMATCH] {v.get('name')!r} value {value!r} not in {actual!r}")
                errors += 1

        status = "OK" if errors == 0 else f"{errors} ERRORS"
        print(f"[{status}] {gold_file.name}")

        if errors:
            all_ok = False

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()