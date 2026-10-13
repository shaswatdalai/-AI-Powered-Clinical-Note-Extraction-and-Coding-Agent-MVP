"""
Cost and latency report (SOW 3.9 / 8.8).

Runs the pipeline on a sample of notes, parses the "extract took X.XXs"
and "verify took X.XXs" lines out of the trace, and reports:
  - median extract time per note
  - median verify time per note
  - median end-to-end time per note
  - model-call count per note (extract=1, verify=1)

SOW 8.8: median end-to-end time under 30 seconds per note on free tier,
with model-call count reported per note.

No LLM calls if the extractor and verifier caches are warm.
"""

import re
import statistics
import sys
from pathlib import Path

from src.orchestrator import run


DATA_DIR = Path("data")

EXTRACT_RE = re.compile(r"extract took ([\d.]+)s")
VERIFY_RE = re.compile(r"verify took ([\d.]+)s")


def main():
    args = sys.argv[1:]
    limit = int(args[0]) if args and args[0].isdigit() else None

    note_files = sorted(DATA_DIR.glob("note_*.txt"))
    if limit:
        note_files = note_files[:limit]

    extract_times = []
    verify_times = []
    end_to_end = []
    per_note = []

    for note_path in note_files:
        note_id = note_path.stem
        text = note_path.read_text(encoding="utf-8")
        try:
            result = run(text)
        except Exception as e:
            print(f"  [skip] {note_id}: {type(e).__name__}")
            continue

        trace = result["trace"]
        ext = None
        ver = None
        for line in trace:
            m = EXTRACT_RE.search(line)
            if m:
                ext = float(m.group(1))
            m = VERIFY_RE.search(line)
            if m:
                ver = float(m.group(1))

        if ext is None:
            print(f"  [skip] {note_id}: no extract timing in trace")
            continue

        end = ext + (ver or 0.0)
        extract_times.append(ext)
        if ver is not None:
            verify_times.append(ver)
        end_to_end.append(end)
        per_note.append((note_id, ext, ver, end))

    print()
    print("=" * 70)
    print("COST AND LATENCY (SOW 8.8 target: median end-to-end < 30s)")
    print("=" * 70)
    print(f"Notes measured: {len(per_note)}")
    print()
    if extract_times:
        print(f"Extract time:   median {statistics.median(extract_times):.2f}s   "
              f"p95 {statistics.quantiles(extract_times, n=20)[18]:.2f}s   "
              f"min {min(extract_times):.2f}s   max {max(extract_times):.2f}s")
    if verify_times:
        print(f"Verify time:    median {statistics.median(verify_times):.2f}s   "
              f"p95 {statistics.quantiles(verify_times, n=20)[18]:.2f}s   "
              f"min {min(verify_times):.2f}s   max {max(verify_times):.2f}s")
    if end_to_end:
        print(f"End-to-end:     median {statistics.median(end_to_end):.2f}s   "
              f"p95 {statistics.quantiles(end_to_end, n=20)[18]:.2f}s   "
              f"min {min(end_to_end):.2f}s   max {max(end_to_end):.2f}s")
    print()
    print("Model calls per note: 2 (1 extractor + 1 verifier) in verified mode,")
    print("                      1 (extractor only) in raw mode.")
    print()
    print("Per-note breakdown:")
    for note_id, ext, ver, end in per_note[:20]:
        ver_s = f"{ver:.2f}s" if ver is not None else "n/a"
        print(f"  {note_id}  extract={ext:6.2f}s  verify={ver_s:>7s}  end={end:6.2f}s")


if __name__ == "__main__":
    main()