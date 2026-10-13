"""
Contradiction-set eval (SOW 3.9 / 8.5).

For each entry in eval_sets/contradiction.json:
  - read the base note
  - inject a contradicting statement into the named section
  - run the pipeline
  - check whether the verifier flagged a contradiction, OR flagged one of
    the planted items with a reason mentioning contradiction / status / denial

SOW 8.5 target: >= 80% of planted contradictions flagged.

Uses the pipeline (uses extractor + verifier caches).
"""

import json
import re
from pathlib import Path

from src.orchestrator import run


SET_PATH = Path("eval_sets/contradiction.json")
DATA_DIR = Path("data")


def _inject(note_text: str, injected: str, section: str) -> str:
    """Insert the injected text after the section heading, or append."""
    pattern = re.compile(
        rf"^({re.escape(section)}[A-Z ]*:,)",
        re.MULTILINE | re.IGNORECASE,
    )
    m = pattern.search(note_text)
    if m:
        insert_at = m.end()
        return note_text[:insert_at] + " " + injected + note_text[insert_at:]
    return note_text + "\n" + injected + "\n"


def _any_planted_flagged(result: dict, planted: list[str]) -> tuple[bool, str]:
    """Check whether the pipeline flagged one of the planted items with a
    contradiction/status/denial-style reason. Returns (matched, reason)."""
    planted_lower = [p.lower() for p in planted]
    # Look through flagged items.
    for f in result["flagged"]:
        reason = (f.get("reason") or "").lower()
        it = f.get("item", {})
        text = (it.get("text") or "").lower() if isinstance(it, dict) else ""
        for p in planted_lower:
            if p in text:
                return True, f"flagged item: {p} ({reason[:80]})"
    # Look through the trace for contradiction lines from the verifier.
    for line in result["trace"]:
        low = line.lower()
        if "contradiction" in low:
            for p in planted_lower:
                if p in low:
                    return True, f"trace: {line[:100]}"
    return False, ""


def main():
    spec = json.loads(SET_PATH.read_text(encoding="utf-8"))
    entries = spec["notes"]

    print(f"Contradiction eval on {len(entries)} notes")
    print("=" * 70)

    passed = 0
    total = 0

    for entry in entries:
        note_id = entry["note_id"]
        base_id = entry["base_note"]
        base_path = DATA_DIR / f"{base_id}.txt"
        if not base_path.exists():
            print(f"  [skip] {note_id}: base {base_id} not found")
            continue

        base_text = base_path.read_text(encoding="utf-8")
        attacked_text = _inject(
            base_text,
            entry["injected_text"],
            entry.get("injection_section", ""),
        )

        try:
            result = run(attacked_text)
        except Exception as e:
            print(f"  ✗ {note_id}: pipeline failed ({type(e).__name__})")
            continue

        total += 1
        matched, why = _any_planted_flagged(result, entry["planted_items"])

        if matched:
            passed += 1
            print(f"  ✓ {note_id}  {entry['contradiction_type']:28s}  {why}")
        else:
            print(f"  ✗ {note_id}  {entry['contradiction_type']:28s}  not flagged")

    print()
    print("=" * 70)
    print(f"SOW 8.5 target: >= 0.80 flagged")
    print(f"Flagged: {passed}/{total} = {passed/total:.3f}" if total else "  no items")


if __name__ == "__main__":
    main()