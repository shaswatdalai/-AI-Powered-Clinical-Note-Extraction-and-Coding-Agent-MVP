"""
Build gold/note_013.json through gold/note_027.json.
Run from project root:  python scripts/build_gold_013_027.py
"""
import json
from pathlib import Path

GOLD_DIR = Path("gold")
DATA_DIR = Path("data")
GOLD_DIR.mkdir(exist_ok=True)


def write_and_verify(note_id: str, data: dict) -> bool:
    note_path = DATA_DIR / f"{note_id}.txt"
    note = note_path.read_text(encoding="utf-8")
    errors = []

    for dx in data.get("diagnoses", []):
        s, e = dx["span"]
        got = note[s:e]
        if got != dx["name_as_written"]:
            errors.append(f"  DX SPAN MISMATCH: {dx['name_as_written']!r} => got {got!r} at [{s},{e}]")

    for med in data.get("medications", []):
        s, e = med["span"]
        got = note[s:e]
        if med["name"].lower() not in got.lower():
            errors.append(f"  MED MISMATCH: {med['name']!r} not in {got!r}")

    for proc in data.get("procedures", []):
        s, e = proc["span"]
        got = note[s:e]
        if proc["name"].lower() not in got.lower():
            errors.append(f"  PROC MISMATCH: {proc['name']!r} not in {got!r}")

    for al in data.get("allergies", []):
        s, e = al["span"]
        got = note[s:e]
        if al["substance"].lower() not in got.lower():
            errors.append(f"  ALLERGY MISMATCH: {al['substance']!r} not in {got!r}")

    for v in data.get("vitals", []):
        s, e = v["span"]
        got = note[s:e]
        if v["value"] not in got:
            errors.append(f"  VITAL MISMATCH: {v['value']!r} not in {got!r}")

    if errors:
        print(f"[ERRORS] {note_id}:")
        for err in errors:
            print(err)
        return False

    out_path = GOLD_DIR / f"{note_id}.json"
    out_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"[WRITTEN] {note_id}.json")
    return True


# ============================================================
# NOTE 013 — Allergy / Immunology
# ============================================================
note_013 = {
    "note_id": "note_013",
    "specialty": "Allergy / Immunology",
    "source_row_index": 4993,
    "diagnoses": [
        {"name_as_written": "xerostomia", "normalised_name": "xerostomia",
         "status": "active", "span": [135, 145], "icd_code": "R68.2"},
        {"name_as_written": "gastroesophageal reflux disease",
         "normalised_name": "gastroesophageal reflux disease",
         "status": "active", "span": [147, 178], "icd_code": "K21.9"},
        {"name_as_written": "possible food allergies", "normalised_name": "food allergies",
         "status": "suspected", "span": [180, 203], "icd_code": None},
        {"name_as_written": "asthma", "normalised_name": "asthma",
         "status": "active", "span": [230, 236], "icd_code": "J45.909"},
        {"name_as_written": "environmental inhalant allergies",
         "normalised_name": "environmental inhalant allergies",
         "status": "active", "span": [242, 274], "icd_code": "J30.1"},
        {"name_as_written": "Chronic glossitis", "normalised_name": "chronic glossitis",
         "status": "active", "span": [394, 411], "icd_code": "K14.0"},
        {"name_as_written": "probable environmental inhalant allergies",
         "normalised_name": "environmental inhalant allergies",
         "status": "suspected", "span": [423, 464], "icd_code": "J30.1"},
        {"name_as_written": "probable food allergies", "normalised_name": "food allergies",
         "status": "suspected", "span": [465, 488], "icd_code": None},
        {"name_as_written": "fibromyalgia", "normalised_name": "fibromyalgia",
         "status": "historical", "span": [523, 535], "icd_code": "M79.3"},
        {"name_as_written": "peptic ulcer disease", "normalised_name": "peptic ulcer disease",
         "status": "historical", "span": [552, 572], "icd_code": "K27.9"},
        {"name_as_written": "gastritis", "normalised_name": "gastritis",
         "status": "historical", "span": [585, 594], "icd_code": "K29.70"},
        {"name_as_written": "gastroesophageal disease",
         "normalised_name": "gastroesophageal reflux disease",
         "status": "historical", "span": [607, 631], "icd_code": "K21.9"},
        {"name_as_written": "chronic fatigue", "normalised_name": "chronic fatigue syndrome",
         "status": "historical", "span": [648, 663], "icd_code": "G93.3"},
        {"name_as_written": "hypothyroidism", "normalised_name": "hypothyroidism",
         "status": "historical", "span": [680, 694], "icd_code": "E03.9"},
        {"name_as_written": "depression", "normalised_name": "depression",
         "status": "historical", "span": [711, 721], "icd_code": "F32.9"},
        {"name_as_written": "dysphagia", "normalised_name": "dysphagia",
         "status": "historical", "span": [738, 747], "icd_code": "R13.10"},
    ],
    "medications": [],
    "procedures": [
        {"name": "RAST allergy testing", "date": None, "span": [768, 788]},
    ],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 014 — Autopsy  (special case: cause-of-death findings only)
# ============================================================
note_014 = {
    "note_id": "note_014",
    "specialty": "Autopsy",
    "source_row_index": 4988,
    "diagnoses": [
        {"name_as_written": "Subdural hematoma",
         "normalised_name": "subdural hematoma",
         "status": "active", "span": [1544, 1561], "icd_code": "S06.4X9A"},
        {"name_as_written": "comminuted fractures of the occipital bone",
         "normalised_name": "comminuted occipital bone fracture",
         "status": "active", "span": [1566, 1608], "icd_code": "S02.119A"},
        {"name_as_written": "Blunt force traumatic injury",
         "normalised_name": "blunt force traumatic injury",
         "status": "active", "span": [2995, 3023], "icd_code": "T14.8XXA"},
        {"name_as_written": "multiple cranial fractures",
         "normalised_name": "multiple cranial fractures",
         "status": "active", "span": [3029, 3055], "icd_code": "S02.91XA"},
        {"name_as_written": "craniocerebral injury",
         "normalised_name": "craniocerebral injury",
         "status": "active", "span": [3069, 3090], "icd_code": "S09.90XA"},
    ],
    "medications": [],
    "procedures": [],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 015 — Bariatrics
# ============================================================
note_015 = {
    "note_id": "note_015",
    "specialty": "Bariatrics",
    "source_row_index": 4985,
    "diagnoses": [
        {"name_as_written": "hypertension", "normalised_name": "hypertension",
         "status": "active", "span": [692, 704], "icd_code": "I10"},
        {"name_as_written": "hypercholesterolemia", "normalised_name": "hypercholesterolemia",
         "status": "active", "span": [709, 729], "icd_code": "E78.00"},
        {"name_as_written": "high cholesterol", "normalised_name": "hypercholesterolemia",
         "status": "active", "span": [863, 879], "icd_code": "E78.00"},
        {"name_as_written": "depression", "normalised_name": "depression",
         "status": "active", "span": [920, 930], "icd_code": "F32.9"},
        {"name_as_written": "DVT", "normalised_name": "deep vein thrombosis",
         "status": "historical", "span": [996, 999], "icd_code": "Z86.718"},
        {"name_as_written": "thyroid disease", "normalised_name": "thyroid disease",
         "status": "historical", "span": [1062, 1077], "icd_code": "E07.9"},
        {"name_as_written": "gallstones", "normalised_name": "cholelithiasis",
         "status": "historical", "span": [1203, 1213], "icd_code": "K80.20"},
        {"name_as_written": "hemorrhoids", "normalised_name": "hemorrhoids",
         "status": "active", "span": [2389, 2400], "icd_code": "K64.9"},
        {"name_as_written": "ulcerative colitis", "normalised_name": "ulcerative colitis",
         "status": "ruled_out", "span": [2490, 2508], "icd_code": "K51.90"},
        {"name_as_written": "Crohn disease", "normalised_name": "crohn disease",
         "status": "ruled_out", "span": [2510, 2523], "icd_code": "K50.90"},
        {"name_as_written": "liver disease", "normalised_name": "liver disease",
         "status": "ruled_out", "span": [2545, 2558], "icd_code": None},
        {"name_as_written": "kidney disease", "normalised_name": "kidney disease",
         "status": "ruled_out", "span": [2563, 2577], "icd_code": None},
        {"name_as_written": "cardiac disease", "normalised_name": "cardiac disease",
         "status": "ruled_out", "span": [2603, 2618], "icd_code": None},
        {"name_as_written": "stroke", "normalised_name": "stroke",
         "status": "ruled_out", "span": [2632, 2638], "icd_code": None},
    ],
    "medications": [
        {"name": "Norvasc", "dose": "10 mg", "route": "PO", "frequency": "daily",
         "status": "current", "span": [1343, 1356]},
        {"name": "Lopressor", "dose": "50 mg", "route": "PO", "frequency": "b.i.d.",
         "status": "current", "span": [1369, 1393]},
        {"name": "lovastatin", "dose": "10 mg", "route": "PO", "frequency": "at bedtime",
         "status": "current", "span": [1407, 1423]},
        {"name": "citalopram", "dose": "10 mg", "route": "PO", "frequency": "daily",
         "status": "current", "span": [1441, 1457]},
        {"name": "aspirin", "dose": "500 mg", "route": "PO", "frequency": "three times a day",
         "status": "discontinued", "span": [1470, 1484]},
        {"name": "vitamin D", "dose": None, "route": None, "frequency": None,
         "status": "current", "span": [1532, 1541]},
        {"name": "Premarin", "dose": "0.3 mg", "route": "PO", "frequency": "daily",
         "status": "discontinued", "span": [1543, 1558]},
        {"name": "omega-3 fatty acids", "dose": None, "route": None, "frequency": None,
         "status": "current", "span": [1601, 1620]},
        {"name": "vitamin D", "dose": "50,000 units", "route": None, "frequency": "q. weekly",
         "status": "current", "span": [1626, 1648]},
        {"name": "Medifast", "dose": None, "route": None, "frequency": None,
         "status": "newly_prescribed", "span": [4201, 4209]},
    ],
    "procedures": [
        {"name": "hysterectomy", "date": "1994", "span": [1025, 1037]},
        {"name": "cholecystectomy", "date": "2008", "span": [1175, 1190]},
        {"name": "upper GI series", "date": None, "span": [3988, 4003]},
    ],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 016 — Cardiovascular / Pulmonary
# (carotid duplex ultrasound report — all findings, no diagnoses/meds/vitals)
# ============================================================
note_016 = {
    "note_id": "note_016",
    "specialty": "Cardiovascular / Pulmonary",
    "source_row_index": 4613,
    "diagnoses": [],
    "medications": [],
    "procedures": [],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 017 — Chiropractic
# (HPI only; no formal diagnoses named; symptoms are ankle/back/neck pain)
# ============================================================
note_017 = {
    "note_id": "note_017",
    "specialty": "Chiropractic",
    "source_row_index": 4606,
    "diagnoses": [],
    "medications": [],
    "procedures": [
        {"name": "x-rays of the lumbar spine, left ankle, and left foot",
         "date": "November 21, 2004", "span": [771, 824]},
    ],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 018 — Consult - History and Phy.
# ============================================================
note_018 = {
    "note_id": "note_018",
    "specialty": "Consult - History and Phy.",
    "source_row_index": 4155,
    "diagnoses": [
        {"name_as_written": "schizoaffective disorder",
         "normalised_name": "schizoaffective disorder",
         "status": "active", "span": [114, 138], "icd_code": "F25.9"},
        {"name_as_written": "diabetes", "normalised_name": "diabetes mellitus",
         "status": "active", "span": [140, 148], "icd_code": "E11.9"},
        {"name_as_written": "osteoarthritis", "normalised_name": "osteoarthritis",
         "status": "active", "span": [150, 164], "icd_code": "M19.90"},
        {"name_as_written": "hypothyroidism", "normalised_name": "hypothyroidism",
         "status": "active", "span": [166, 180], "icd_code": "E03.9"},
        {"name_as_written": "GERD", "normalised_name": "gastroesophageal reflux disease",
         "status": "active", "span": [182, 186], "icd_code": "K21.9"},
        {"name_as_written": "dyslipidemia", "normalised_name": "dyslipidemia",
         "status": "active", "span": [192, 204], "icd_code": "E78.5"},
        {"name_as_written": "bipolar disorder", "normalised_name": "bipolar disorder",
         "status": "historical", "span": [1976, 1992], "icd_code": "F31.9"},
        {"name_as_written": "schizophrenia", "normalised_name": "schizophrenia",
         "status": "historical", "span": [2024, 2037], "icd_code": "F20.9"},
    ],
    "medications": [
        {"name": "Zyprexa", "dose": None, "route": None, "frequency": None,
         "status": "discontinued", "span": [463, 470]},
        {"name": "lithium", "dose": None, "route": None, "frequency": None,
         "status": "discontinued", "span": [475, 482]},
        {"name": "Seroquel", "dose": "100 mg", "route": "PO", "frequency": "b.i.d.",
         "status": "current", "span": [2166, 2174]},
        {"name": "Risperdal", "dose": "1 mg", "route": "PO", "frequency": "t.i.d.",
         "status": "current", "span": [2412, 2421]},
        {"name": "Actos", "dose": "30 mg", "route": "PO", "frequency": "daily",
         "status": "current", "span": [2450, 2455]},
        {"name": "Lipitor", "dose": "10 mg", "route": "PO", "frequency": "at bedtime",
         "status": "current", "span": [2481, 2488]},
        {"name": "Gabapentin", "dose": "100 mg", "route": "PO", "frequency": "b.i.d.",
         "status": "current", "span": [2519, 2529]},
        {"name": "Glimepiride", "dose": "2 mg", "route": "PO", "frequency": "b.i.d.",
         "status": "current", "span": [2556, 2567]},
        {"name": "Levothyroxine", "dose": "25 mcg", "route": "PO", "frequency": "q.a.m.",
         "status": "current", "span": [2592, 2605]},
        {"name": "Protonix", "dose": "40 mg", "route": "PO", "frequency": "daily",
         "status": "current", "span": [2632, 2640]},
    ],
    "procedures": [],
    "allergies": [],
    "vitals": [
        {"name": "BP", "value": "152/92", "unit": "mmHg", "span": [4622, 4628]},
        {"name": "HR", "value": "81", "unit": "bpm", "span": [4630, 4643]},
        {"name": "Temp", "value": "97.2", "unit": "°F", "span": [4661, 4665]},
    ],
}

# ============================================================
# NOTE 019 — Cosmetic / Plastic Surgery
# ============================================================
note_019 = {
    "note_id": "note_019",
    "specialty": "Cosmetic / Plastic Surgery",
    "source_row_index": 4056,
    "diagnoses": [
        {"name_as_written": "personal history of breast cancer",
         "normalised_name": "breast cancer",
         "status": "historical", "span": [71, 104], "icd_code": "Z85.3"},
        {"name_as_written": "Breast asymmetry", "normalised_name": "breast asymmetry",
         "status": "active", "span": [110, 126], "icd_code": "N65.1"},
    ],
    "medications": [],
    "procedures": [
        {"name": "Left nipple areolar reconstruction", "date": None, "span": [271, 305]},
        {"name": "full-thickness skin graft", "date": None, "span": [318, 343]},
        {"name": "Redo right mastopexy", "date": None, "span": [369, 389]},
    ],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 020 — Dentistry
# ============================================================
note_020 = {
    "note_id": "note_020",
    "specialty": "Dentistry",
    "source_row_index": 4044,
    "diagnoses": [
        {"name_as_written": "Severe dental caries", "normalised_name": "dental caries",
         "status": "active", "span": [134, 154], "icd_code": "K02.9"},
        {"name_as_written": "Hemophilia", "normalised_name": "hemophilia",
         "status": "active", "span": [160, 170], "icd_code": "D66"},
        {"name_as_written": "Nonrestorable teeth", "normalised_name": "nonrestorable teeth",
         "status": "active", "span": [245, 264], "icd_code": None},
    ],
    "medications": [
        {"name": "Tylenol with Codeine", "dose": None, "route": "PO", "frequency": None,
         "status": "newly_prescribed", "span": [5352, 5372]},
    ],
    "procedures": [
        {"name": "Full mouth dental rehabilitation", "date": None, "span": [23, 55]},
    ],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 021 — Dermatology
# ============================================================
note_021 = {
    "note_id": "note_021",
    "specialty": "Dermatology",
    "source_row_index": 4024,
    "diagnoses": [
        {"name_as_written": "Buttock abscess", "normalised_name": "buttock abscess",
         "status": "active", "span": [19, 34], "icd_code": "L02.31"},
        {"name_as_written": "Diabetes type II", "normalised_name": "type 2 diabetes mellitus",
         "status": "active", "span": [569, 585], "icd_code": "E11.9"},
        {"name_as_written": "high cholesterol", "normalised_name": "hypercholesterolemia",
         "status": "active", "span": [606, 622], "icd_code": "E78.00"},
    ],
    "medications": [
        {"name": "Insulin", "dose": None, "route": None, "frequency": None,
         "status": "current", "span": [721, 728]},
        {"name": "metformin", "dose": None, "route": None, "frequency": None,
         "status": "current", "span": [730, 739]},
        {"name": "Glucotrol", "dose": None, "route": None, "frequency": None,
         "status": "current", "span": [741, 750]},
        {"name": "Lipitor", "dose": None, "route": None, "frequency": None,
         "status": "current", "span": [756, 763]},
    ],
    "procedures": [
        {"name": "incision and drainage", "date": None, "span": [339, 360]},
        {"name": "C-section", "date": None, "span": [649, 658]},
        {"name": "D&C", "date": None, "span": [663, 666]},
    ],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 022 — Diets and Nutritions
# (No formal diagnoses; weight-loss follow-up note only)
# ============================================================
note_022 = {
    "note_id": "note_022",
    "specialty": "Diets and Nutritions",
    "source_row_index": 3996,
    "diagnoses": [],
    "medications": [],
    "procedures": [],
    "allergies": [],
    "vitals": [
        {"name": "Weight", "value": "186-1/2", "unit": "pounds", "span": [193, 200]},
    ],
}

# ============================================================
# NOTE 023 — Discharge Summary
# ============================================================
note_023 = {
    "note_id": "note_023",
    "specialty": "Discharge Summary",
    "source_row_index": 3973,
    "diagnoses": [
        {"name_as_written": "Cholecystitis", "normalised_name": "cholecystitis",
         "status": "active", "span": [24, 37], "icd_code": "K81.9"},
        {"name_as_written": "choledocholithiasis", "normalised_name": "choledocholithiasis",
         "status": "active", "span": [43, 62], "icd_code": "K80.50"},
        {"name_as_written": "sleep apnea", "normalised_name": "sleep apnea",
         "status": "historical", "span": [287, 298], "icd_code": "G47.30"},
        {"name_as_written": "Morbid obesity", "normalised_name": "morbid obesity",
         "status": "active", "span": [346, 360], "icd_code": "E66.01"},
    ],
    "medications": [
        {"name": "iron", "dose": "325 mg", "route": "PO", "frequency": "t.i.d.",
         "status": "newly_prescribed", "span": [2620, 2631]},
        {"name": "Lortab", "dose": "15 cc", "route": "PO", "frequency": "q.4 h. p.r.n.",
         "status": "newly_prescribed", "span": [2648, 2661]},
    ],
    "procedures": [
        {"name": "roux-en-y gastric bypass", "date": "01/07", "span": [160, 184]},
        {"name": "Laparoscopic paraventral hernia", "date": "11/07", "span": [230, 261]},
        {"name": "common bile duct exploration", "date": None, "span": [466, 494]},
        {"name": "Laparoscopic cholecystectomy", "date": None, "span": [402, 430]},
        {"name": "HIDA scan", "date": None, "span": [819, 828]},
    ],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 024 — ENT - Otolaryngology
# ============================================================
note_024 = {
    "note_id": "note_024",
    "specialty": "ENT - Otolaryngology",
    "source_row_index": 3696,
    "diagnoses": [
        {"name_as_written": "Ventilator-dependent respiratory failure",
         "normalised_name": "ventilator-dependent respiratory failure",
         "status": "active", "span": [28, 68], "icd_code": "J96.00"},
        {"name_as_written": "Multiple strokes", "normalised_name": "stroke",
         "status": "active", "span": [74, 90], "icd_code": "I63.9"},
    ],
    "medications": [],
    "procedures": [
        {"name": "Tracheostomy", "date": None, "span": [211, 223]},
        {"name": "Thyroid isthmusectomy", "date": None, "span": [229, 250]},
    ],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 025 — Emergency Room Reports
# ============================================================
note_025 = {
    "note_id": "note_025",
    "specialty": "Emergency Room Reports",
    "source_row_index": 3846,
    "diagnoses": [
        {"name_as_written": "Hypertension", "normalised_name": "hypertension",
         "status": "historical", "span": [397, 409], "icd_code": "I10"},
    ],
    "medications": [
        {"name": "banana bag", "dose": None, "route": "IV", "frequency": None,
         "status": "newly_prescribed", "span": [1748, 1758]},
    ],
    "procedures": [
        {"name": "X-rays of the C spine", "date": None, "span": [1425, 1446]},
    ],
    "allergies": [],
    "vitals": [
        {"name": "BP", "value": "165/95", "unit": "mmHg", "span": [610, 616]},
        {"name": "HR", "value": "80", "unit": "bpm", "span": [620, 622]},
        {"name": "RR", "value": "12", "unit": "breaths/min", "span": [626, 628]},
        {"name": "Temp", "value": "98.4", "unit": "°F", "span": [634, 638]},
        {"name": "SpO2", "value": "95%", "unit": "%", "span": [644, 647]},
    ],
}

# ============================================================
# NOTE 026 — Endocrinology  (actually a head/neck surgery op note)
# ============================================================
note_026 = {
    "note_id": "note_026",
    "specialty": "Endocrinology",
    "source_row_index": 3794,
    "diagnoses": [
        {"name_as_written": "squamous cell carcinoma of his glottic larynx",
         "normalised_name": "squamous cell carcinoma of the larynx",
         "status": "historical", "span": [237, 282], "icd_code": "C32.0"},
        {"name_as_written": "Squamous cell carcinoma of the larynx",
         "normalised_name": "squamous cell carcinoma of the larynx",
         "status": "active", "span": [1370, 1407], "icd_code": "C32.0"},
    ],
    "medications": [],
    "procedures": [
        {"name": "Total laryngectomy", "date": None, "span": [22, 40]},
        {"name": "right level 2, 3, 4 neck dissection", "date": None, "span": [42, 77]},
        {"name": "tracheoesophageal puncture", "date": None, "span": [79, 105]},
        {"name": "cricopharyngeal myotomy", "date": None, "span": [107, 130]},
        {"name": "right thyroid lobectomy", "date": None, "span": [132, 155]},
        {"name": "laser excision", "date": "06/07", "span": [311, 325]},
        {"name": "Direct laryngoscopy", "date": None, "span": [1760, 1779]},
    ],
    "allergies": [],
    "vitals": [],
}

# ============================================================
# NOTE 027 — Gastroenterology
# ============================================================
note_027 = {
    "note_id": "note_027",
    "specialty": "Gastroenterology",
    "source_row_index": 3512,
    "diagnoses": [
        {"name_as_written": "Appendicitis", "normalised_name": "appendicitis",
         "status": "active", "span": [26, 38], "icd_code": "K37"},
    ],
    "medications": [],
    "procedures": [
        {"name": "Laparoscopic appendectomy", "date": None, "span": [104, 129]},
    ],
    "allergies": [],
    "vitals": [],
}


# ============================================================
# Write all notes
# ============================================================
all_notes = [
    ("note_013", note_013),
    ("note_014", note_014),
    ("note_015", note_015),
    ("note_016", note_016),
    ("note_017", note_017),
    ("note_018", note_018),
    ("note_019", note_019),
    ("note_020", note_020),
    ("note_021", note_021),
    ("note_022", note_022),
    ("note_023", note_023),
    ("note_024", note_024),
    ("note_025", note_025),
    ("note_026", note_026),
    ("note_027", note_027),
]

all_ok = True
for note_id, data in all_notes:
    ok = write_and_verify(note_id, data)
    if not ok:
        all_ok = False

print()
if all_ok:
    print("All 15 gold files written and spans verified.")
else:
    print("Some files had errors — fix before running verify_gold.py")
