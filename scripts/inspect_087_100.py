import json
from pathlib import Path

for i in range(87, 101):
    note_id = f"note_{i:03d}"
    meta_path = Path(f"data/{note_id}.meta.json")
    text_path = Path(f"data/{note_id}.txt")
    if not meta_path.exists() or not text_path.exists():
        print(f"MISSING: {note_id}")
        continue
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    text = text_path.read_text(encoding="utf-8")
    print(f"{note_id}: specialty={meta['specialty']!r}, row={meta['original_index']}, length={len(text)} chars, lines={len(text.splitlines())}")
