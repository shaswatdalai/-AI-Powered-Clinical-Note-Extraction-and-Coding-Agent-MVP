import json
from pathlib import Path

valid_dx_status = {"active", "historical", "ruled_out", "suspected"}
valid_med_status = {"current", "discontinued", "newly_prescribed"}

report = []

for i in range(28, 43):
    nid = f"note_{i:03d}"
    gpath = Path(f"gold/{nid}.json")
    mpath = Path(f"data/{nid}.meta.json")
    tpath = Path(f"data/{nid}.txt")

    data = json.loads(gpath.read_text(encoding="utf-8"))
    meta = json.loads(mpath.read_text(encoding="utf-8"))
    txt = tpath.read_text(encoding="utf-8")

    assert data["note_id"] == nid
    assert data["specialty"] == meta["specialty"].strip(), f"{data['specialty']} != {meta['specialty'].strip()}"
    assert data["source_row_index"] == meta["original_index"]

    dx_count = len(data["diagnoses"])
    med_count = len(data["medications"])
    proc_count = len(data["procedures"])
    al_count = len(data["allergies"])
    vit_count = len(data["vitals"])

    for dx in data["diagnoses"]:
        assert dx["status"] in valid_dx_status, dx["status"]
        s, e = dx["span"]
        assert txt[s:e] == dx["name_as_written"], f"DX mismatch: {txt[s:e]!r} != {dx['name_as_written']!r}"
        assert "normalised_name" in dx
        assert "icd_code" in dx

    for med in data["medications"]:
        assert med["status"] in valid_med_status, med["status"]
        s, e = med["span"]
        assert med["name"].lower() in txt[s:e].lower(), f"MED mismatch: {med['name']!r} not in {txt[s:e]!r}"
        assert "dose" in med and "route" in med and "frequency" in med

    for proc in data["procedures"]:
        s, e = proc["span"]
        assert proc["name"].lower() in txt[s:e].lower(), f"PROC mismatch: {proc['name']!r} not in {txt[s:e]!r}"
        assert "date" in proc

    for al in data["allergies"]:
        s, e = al["span"]
        assert al["substance"].lower() in txt[s:e].lower(), f"ALLERGY mismatch: {al['substance']!r} not in {txt[s:e]!r}"
        assert "reaction" in al

    for v in data["vitals"]:
        s, e = v["span"]
        assert v["value"] in txt[s:e], f"VITAL mismatch: {v['value']!r} not in {txt[s:e]!r}"
        assert "name" in v and "unit" in v

    report.append({
        "note_id": nid,
        "specialty": data["specialty"],
        "row": data["source_row_index"],
        "diagnoses": dx_count,
        "medications": med_count,
        "procedures": proc_count,
        "allergies": al_count,
        "vitals": vit_count,
    })

print(f"{'Note':<10} {'Specialty':<30} {'Dx':<4} {'Meds':<5} {'Procs':<6} {'Allerg':<7} {'Vitals':<6}")
print("-" * 75)
for r in report:
    print(f"{r['note_id']:<10} {r['specialty']:<30} {r['diagnoses']:<4} {r['medications']:<5} {r['procedures']:<6} {r['allergies']:<7} {r['vitals']:<6}")
print("\nAll 15 files strictly validated against schema!")
