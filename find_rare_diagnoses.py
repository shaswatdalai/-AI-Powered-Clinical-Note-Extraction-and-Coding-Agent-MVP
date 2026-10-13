"""
Find gold notes whose diagnoses do NOT confidently match the ICD index.

A diagnosis is considered "rare or unmappable" if icd_lookup returns
NO_CONFIDENT_MATCH. Uses the token-overlap gate in src/icd_index.py.

No LLM calls. icd_lookup runs locally.
"""

import json
import glob
from src.icd_index import load_index, icd_lookup


load_index()

candidates = []

for f in sorted(glob.glob("gold/note_*.json")):
    note_id = f.split("note_")[1].split(".")[0]
    g = json.loads(open(f, encoding="utf-8").read())
    dxs = g.get("diagnoses", [])
    rare = []
    for d in dxs:
        name = d.get("normalised_name") or d.get("name_as_written")
        if not name:
            continue
        res = icd_lookup(name)
        if isinstance(res, str) and res == "NO_CONFIDENT_MATCH":
            rare.append({
                "name": name,
                "span": d.get("span"),
                "gold_icd": d.get("icd_code"),
            })
    if rare:
        candidates.append({
            "note_id": f"note_{note_id}",
            "rare_diagnoses": rare,
            "total_diagnoses": len(dxs),
        })

print(f"{len(candidates)} notes have at least one rare/unmappable diagnosis")
print()
for c in candidates:
    names = ", ".join(r["name"] for r in c["rare_diagnoses"])
    print(f"  {c['note_id']}  ({len(c['rare_diagnoses'])}/{c['total_diagnoses']} rare)  {names}")