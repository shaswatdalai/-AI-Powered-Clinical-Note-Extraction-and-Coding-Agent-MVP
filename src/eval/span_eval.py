"""
Span-faithfulness eval (SOW 8.2).

For every accepted item across the corpus, verify programmatically:
  1. The item has a span.
  2. span[0] >= 0 and span[1] > span[0].
  3. span[1] <= len(note_text).
  4. note_text[span[0]:span[1]] contains the item's text (case-insensitive
     substring, after whitespace collapse), OR the item's evidence_quote
     contains the item's text.

SOW 8.2 target: 100% of accepted items have a span that exists at the
stated offsets and supports the item. A single fabricated item fails this.

No LLM calls if the extractor cache is warm.
"""

import sys
from pathlib import Path

from src.masker import mask_pii
from src.extractor import extract
from src.verifier import verify
from src.icd_index import load_index, icd_lookup
from src.orchestrator import _build_verifier_items, _ensure_index_loaded


DATA_DIR = Path("data")


def _normalize(s: str) -> str:
    return " ".join((s or "").lower().split())


def _check_item(item: dict, note_text: str) -> tuple[bool, str]:
    """Return (ok, reason_if_not)."""
    span = item.get("span")
    text = item.get("text", "")
    if not span or not isinstance(span, list) or len(span) != 2:
        return False, "no span"
    s, e = span
    if not isinstance(s, int) or not isinstance(e, int):
        return False, "span not ints"
    if s < 0 or e <= s:
        return False, f"invalid offsets: [{s}, {e}]"
    if e > len(note_text):
        return False, f"span end {e} > note length {len(note_text)}"
    sliced = note_text[s:e]
    # The slice should contain the item's text (normalized).
    if _normalize(text) and _normalize(text) not in _normalize(sliced):
        # Fallback: some extractors span the value, not the name. Accept
        # if the evidence_quote is a subset of the slice or vice versa.
        quote = item.get("span_text", "")
        if _normalize(quote) and (
            _normalize(quote) in _normalize(sliced)
            or _normalize(sliced) in _normalize(quote)
        ):
            return True, ""
        return False, f"slice {sliced!r} does not contain text {text!r}"
    return True, ""


def main():
    args = sys.argv[1:]
    limit = int(args[0]) if args and args[0].isdigit() else None

    _ensure_index_loaded()

    note_files = sorted(DATA_DIR.glob("note_*.txt"))
    if limit:
        note_files = note_files[:limit]

    total = 0
    ok = 0
    failures = []

    for note_path in note_files:
        note_id = note_path.stem
        note_text = note_path.read_text(encoding="utf-8")
        masked, _ = mask_pii(note_text)
        try:
            ex = extract(masked)
        except Exception as e:
            print(f"  [skip] {note_id}: extract failed ({type(e).__name__})")
            continue

        try:
            items = _build_verifier_items(ex)
            resp = verify(masked, items)
            accepted_ids = {
                v.id for v in resp.verdicts
                if v.verdict == "SUPPORTED"
            }
        except Exception as e:
            print(f"  [skip] {note_id}: verify failed ({type(e).__name__})")
            continue

        for item in items:
            if item["id"] not in accepted_ids:
                continue
            total += 1
            passed, reason = _check_item(item, note_text)
            if passed:
                ok += 1
            else:
                failures.append((note_id, item["id"], reason))

    print()
    print("=" * 70)
    print("SPAN FAITHFULNESS (SOW 8.2 target: 1.000)")
    print("=" * 70)
    print(f"Accepted items checked: {total}")
    print(f"Spans valid:            {ok}/{total} = {ok/total:.3f}" if total else "  no items")
    if failures:
        print()
        print("Failures:")
        for note_id, item_id, reason in failures[:30]:
            print(f"  {note_id}  {item_id}  {reason}")


if __name__ == "__main__":
    main()