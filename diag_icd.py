import json
import glob
from src.icd_index import load_index, icd_lookup

load_index()

targets = [
    "ligature mark",
    "hyoid bone fracture",
    "status post lap band placement",
    "stapedial fixation due to otosclerosis",
    "blunt force traumatic injury",
    "hypertension",
    "asthma",
]

for name in targets:
    res = icd_lookup(name)
    print("=" * 70)
    print(f"QUERY: {name!r}")
    if not res:
        print("  (empty)")
        continue
    for c in res[:3]:
        if isinstance(c, dict):
            code = c.get("code")
            score = c.get("score")
            tc = c.get("top_cosine")
            desc = (c.get("description") or "")[:100]
            print(f"  {code:8s} score={score} top_cosine={tc}")
            print(f"           {desc}")
        else:
            print(f"  raw: {c}")