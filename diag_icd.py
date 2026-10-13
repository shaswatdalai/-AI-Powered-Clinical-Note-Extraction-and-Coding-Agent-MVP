import json
import glob
from src.icd_index import (
    load_index, icd_lookup,
    _vector_search, _bm25_descs, _bm25_codes,
    _meaningful_tokens, MIN_TOKEN_OVERLAP, MIN_COSINE_FLOOR,
)

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
    print("=" * 70)
    print(f"QUERY: {name!r}")

    vr = _vector_search(name)
    if not vr:
        print("  no vector results")
        continue

    top_idx, top_cosine = vr[0]
    code = _bm25_codes[top_idx]
    desc = _bm25_descs[top_idx]
    print(f"  top-1 vector: {code}  cos={top_cosine:.4f}")
    print(f"                {desc!r}")
    print(f"  query tokens: {sorted(_meaningful_tokens(name))}")
    print(f"  cand tokens:  {sorted(_meaningful_tokens(desc))}")
    q = _meaningful_tokens(name)
    c = _meaningful_tokens(desc)
    overlap = len(q & c) / len(q) if q else 0.0
    print(f"  overlap = {overlap:.3f}  (threshold {MIN_TOKEN_OVERLAP})")
    print(f"  cosine gate: {top_cosine:.4f} >= {MIN_COSINE_FLOOR}? {top_cosine >= MIN_COSINE_FLOOR}")

    res = icd_lookup(name)
    if isinstance(res, str):
        print(f"  -> RETURNED STRING: {res!r}")
    else:
        print(f"  -> returned {len(res)} candidates")
        for c in res[:3]:
            print(f"     {c['code']:8s} score={c['score']} cos={c.get('top_cosine')}  {c['description'][:80]}")