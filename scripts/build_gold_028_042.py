"""
Build gold/note_028.json through gold/note_042.json.
Run from project root: python scripts/build_gold_028_042.py
"""
import json
import subprocess
from pathlib import Path

GOLD_DIR = Path("gold")
DATA_DIR = Path("data")
GOLD_DIR.mkdir(exist_ok=True)


def get_span(note: str, phrase: str) -> list[int]:
    start = note.find(phrase)
    assert start != -1, f"Phrase {phrase!r} not found in note"
    end = start + len(phrase)
    assert note[start:end] == phrase
    return [start, end]


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
# NOTE 028 — Allergy / Immunology
# ============================================================
def build_note_028():
    note = (DATA_DIR / "note_028.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_028",
        "specialty": "Allergy / Immunology",
        "source_row_index": 4995,
        "diagnoses": [
            {
                "name_as_written": "Kawasaki disease",
                "normalised_name": "kawasaki disease",
                "status": "active",
                "span": get_span(note, "Kawasaki disease"),
                "icd_code": "M30.3",
            },
            {
                "name_as_written": "mild arthritis",
                "normalised_name": "arthritis",
                "status": "active",
                "span": get_span(note, "mild arthritis"),
                "icd_code": "M13.90",
            },
            {
                "name_as_written": "thrombocytosis",
                "normalised_name": "thrombocytosis",
                "status": "active",
                "span": get_span(note, "thrombocytosis"),
                "icd_code": "D75.2",
            },
        ],
        "medications": [
            {
                "name": "aspirin",
                "dose": "high dose",
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "aspirin"),
            },
            {
                "name": "IVIG",
                "dose": None,
                "route": "IV",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "IVIG"),
            },
            {
                "name": "Prevacid",
                "dose": "15 mg",
                "route": "p.o.",
                "frequency": "once a day",
                "status": "newly_prescribed",
                "span": get_span(note, "Prevacid"),
            },
        ],
        "procedures": [
            {
                "name": "Echocardiogram",
                "date": None,
                "span": get_span(note, "Echocardiogram"),
            }
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "Temp",
                "value": "102",
                "unit": "°F",
                "span": get_span(note, "102"),
            }
        ],
    }


# ============================================================
# NOTE 029 — Autopsy (SPECIAL CASE: major cause of death only)
# ============================================================
def build_note_029():
    note = (DATA_DIR / "note_029.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_029",
        "specialty": "Autopsy",
        "source_row_index": 4990,
        "diagnoses": [
            {
                "name_as_written": "Widespread bronchopneumonia",
                "normalised_name": "bronchopneumonia",
                "status": "active",
                "span": get_span(note, "Widespread bronchopneumonia"),
                "icd_code": "J18.0",
            },
            {
                "name_as_written": "Tubular necrosis",
                "normalised_name": "acute tubular necrosis",
                "status": "active",
                "span": get_span(note, "Tubular necrosis"),
                "icd_code": "N17.0",
            },
        ],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [
            {
                "name": "Length",
                "value": "62",
                "unit": "inches",
                "span": get_span(note, "62-inch"),
            },
            {
                "name": "Weight",
                "value": "112",
                "unit": "pounds",
                "span": get_span(note, "112-pound"),
            },
        ],
    }


# ============================================================
# NOTE 030 — Bariatrics
# ============================================================
def build_note_030():
    note = (DATA_DIR / "note_030.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_030",
        "specialty": "Bariatrics",
        "source_row_index": 1,
        "diagnoses": [
            {
                "name_as_written": "gastroesophageal reflux disease",
                "normalised_name": "gastroesophageal reflux disease",
                "status": "active",
                "span": get_span(note, "gastroesophageal reflux disease"),
                "icd_code": "K21.9",
            },
            {
                "name_as_written": "heart attack",
                "normalised_name": "myocardial infarction",
                "status": "ruled_out",
                "span": get_span(note, "heart attack"),
                "icd_code": "I21.9",
            },
            {
                "name_as_written": "coronary artery disease",
                "normalised_name": "coronary artery disease",
                "status": "ruled_out",
                "span": get_span(note, "coronary artery disease"),
                "icd_code": "I25.10",
            },
            {
                "name_as_written": "congestive heart failure",
                "normalised_name": "congestive heart failure",
                "status": "ruled_out",
                "span": get_span(note, "congestive heart failure"),
                "icd_code": "I50.9",
            },
            {
                "name_as_written": "arrhythmia",
                "normalised_name": "arrhythmia",
                "status": "ruled_out",
                "span": get_span(note, "arrhythmia"),
                "icd_code": "I49.9",
            },
            {
                "name_as_written": "atrial fibrillation",
                "normalised_name": "atrial fibrillation",
                "status": "ruled_out",
                "span": get_span(note, "atrial fibrillation"),
                "icd_code": "I48.91",
            },
            {
                "name_as_written": "high cholesterol",
                "normalised_name": "hypercholesterolemia",
                "status": "ruled_out",
                "span": get_span(note, "high cholesterol"),
                "icd_code": "E78.00",
            },
            {
                "name_as_written": "pulmonary embolism",
                "normalised_name": "pulmonary embolism",
                "status": "ruled_out",
                "span": get_span(note, "pulmonary embolism"),
                "icd_code": "I26.99",
            },
            {
                "name_as_written": "high blood pressure",
                "normalised_name": "hypertension",
                "status": "ruled_out",
                "span": get_span(note, "high blood pressure"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "CVA",
                "normalised_name": "cerebrovascular accident",
                "status": "ruled_out",
                "span": get_span(note, "CVA"),
                "icd_code": "I63.9",
            },
            {
                "name_as_written": "venous insufficiency",
                "normalised_name": "venous insufficiency",
                "status": "ruled_out",
                "span": get_span(note, "venous insufficiency"),
                "icd_code": "I87.2",
            },
            {
                "name_as_written": "thrombophlebitis",
                "normalised_name": "thrombophlebitis",
                "status": "ruled_out",
                "span": get_span(note, "thrombophlebitis"),
                "icd_code": "I80.9",
            },
            {
                "name_as_written": "asthma",
                "normalised_name": "asthma",
                "status": "ruled_out",
                "span": get_span(note, "asthma"),
                "icd_code": "J45.909",
            },
            {
                "name_as_written": "COPD",
                "normalised_name": "chronic obstructive pulmonary disease",
                "status": "ruled_out",
                "span": get_span(note, "COPD"),
                "icd_code": "J44.9",
            },
            {
                "name_as_written": "emphysema",
                "normalised_name": "emphysema",
                "status": "ruled_out",
                "span": get_span(note, "emphysema"),
                "icd_code": "J43.9",
            },
            {
                "name_as_written": "sleep apnea",
                "normalised_name": "sleep apnea",
                "status": "ruled_out",
                "span": get_span(note, "sleep apnea"),
                "icd_code": "G47.30",
            },
            {
                "name_as_written": "diabetes",
                "normalised_name": "diabetes mellitus",
                "status": "ruled_out",
                "span": get_span(note, "diabetes"),
                "icd_code": "E11.9",
            },
            {
                "name_as_written": "osteoarthritis",
                "normalised_name": "osteoarthritis",
                "status": "ruled_out",
                "span": get_span(note, "osteoarthritis"),
                "icd_code": "M19.90",
            },
            {
                "name_as_written": "rheumatoid arthritis",
                "normalised_name": "rheumatoid arthritis",
                "status": "ruled_out",
                "span": get_span(note, "rheumatoid arthritis"),
                "icd_code": "M06.9",
            },
            {
                "name_as_written": "hiatal hernia",
                "normalised_name": "hiatal hernia",
                "status": "ruled_out",
                "span": get_span(note, "hiatal hernia"),
                "icd_code": "K44.9",
            },
            {
                "name_as_written": "peptic ulcer disease",
                "normalised_name": "peptic ulcer disease",
                "status": "ruled_out",
                "span": get_span(note, "peptic ulcer disease"),
                "icd_code": "K27.9",
            },
            {
                "name_as_written": "gallstones",
                "normalised_name": "cholelithiasis",
                "status": "ruled_out",
                "span": get_span(note, "gallstones"),
                "icd_code": "K80.20",
            },
            {
                "name_as_written": "infected gallbladder",
                "normalised_name": "cholecystitis",
                "status": "ruled_out",
                "span": get_span(note, "infected gallbladder"),
                "icd_code": "K81.9",
            },
            {
                "name_as_written": "pancreatitis",
                "normalised_name": "pancreatitis",
                "status": "ruled_out",
                "span": get_span(note, "pancreatitis"),
                "icd_code": "K85.90",
            },
            {
                "name_as_written": "fatty liver",
                "normalised_name": "fatty liver",
                "status": "ruled_out",
                "span": get_span(note, "fatty liver"),
                "icd_code": "K76.0",
            },
            {
                "name_as_written": "hepatitis",
                "normalised_name": "hepatitis",
                "status": "ruled_out",
                "span": get_span(note, "hepatitis"),
                "icd_code": "K75.9",
            },
            {
                "name_as_written": "hemorrhoids",
                "normalised_name": "hemorrhoids",
                "status": "ruled_out",
                "span": get_span(note, "hemorrhoids"),
                "icd_code": "K64.9",
            },
            {
                "name_as_written": "polyps",
                "normalised_name": "polyps",
                "status": "ruled_out",
                "span": get_span(note, "polyps"),
                "icd_code": "K63.5",
            },
            {
                "name_as_written": "urinary stress incontinence",
                "normalised_name": "stress incontinence",
                "status": "ruled_out",
                "span": get_span(note, "urinary stress incontinence"),
                "icd_code": "N39.3",
            },
            {
                "name_as_written": "cancer",
                "normalised_name": "cancer",
                "status": "ruled_out",
                "span": get_span(note, "cancer"),
                "icd_code": "C80.1",
            },
            {
                "name_as_written": "cellulitis",
                "normalised_name": "cellulitis",
                "status": "ruled_out",
                "span": get_span(note, "cellulitis"),
                "icd_code": "L03.90",
            },
            {
                "name_as_written": "pseudotumor cerebri",
                "normalised_name": "pseudotumor cerebri",
                "status": "ruled_out",
                "span": get_span(note, "pseudotumor cerebri"),
                "icd_code": "G93.2",
            },
            {
                "name_as_written": "meningitis",
                "normalised_name": "meningitis",
                "status": "ruled_out",
                "span": get_span(note, "meningitis"),
                "icd_code": "G03.9",
            },
            {
                "name_as_written": "encephalitis",
                "normalised_name": "encephalitis",
                "status": "ruled_out",
                "span": get_span(note, "encephalitis"),
                "icd_code": "G04.90",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "reconstructive surgery on his right hand",
                "date": "13 years ago",
                "span": get_span(note, "reconstructive surgery on his right hand"),
            }
        ],
        "allergies": [
            {
                "substance": "Penicillin",
                "reaction": None,
                "span": get_span(note, "Penicillin"),
            }
        ],
        "vitals": [
            {
                "name": "Weight",
                "value": "312",
                "unit": "pounds",
                "span": get_span(note, "312 pounds"),
            }
        ],
    }


# ============================================================
# NOTE 031 — Cardiovascular / Pulmonary
# ============================================================
def build_note_031():
    note = (DATA_DIR / "note_031.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_031",
        "specialty": "Cardiovascular / Pulmonary",
        "source_row_index": 4926,
        "diagnoses": [],
        "medications": [
            {
                "name": "papaverine",
                "dose": None,
                "route": "topical",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "papaverine"),
            },
            {
                "name": "heparin",
                "dose": None,
                "route": "IV",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "heparinized"),
            },
            {
                "name": "Protamine",
                "dose": None,
                "route": "IV",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Protamine"),
            },
        ],
        "procedures": [
            {
                "name": "Redo coronary bypass grafting x3",
                "date": None,
                "span": get_span(note, "Redo coronary bypass grafting x3"),
            },
            {
                "name": "Placement of a right femoral intraaortic balloon pump",
                "date": None,
                "span": get_span(note, "Placement of a right femoral intraaortic balloon pump"),
            },
            {
                "name": "Total cardiopulmonary bypass",
                "date": None,
                "span": get_span(note, "Total cardiopulmonary bypass"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 032 — Chiropractic
# ============================================================
def build_note_032():
    note = (DATA_DIR / "note_032.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_032",
        "specialty": "Chiropractic",
        "source_row_index": 4610,
        "diagnoses": [
            {
                "name_as_written": "sprain-thoracic",
                "normalised_name": "thoracic sprain",
                "status": "historical",
                "span": get_span(note, "sprain-thoracic"),
                "icd_code": "S23.3XXA",
            },
            {
                "name_as_written": "back pain",
                "normalised_name": "back pain",
                "status": "active",
                "span": get_span(note, "back pain"),
                "icd_code": "M54.5",
            },
            {
                "name_as_written": "degenerative disc disease",
                "normalised_name": "degenerative disc disease",
                "status": "active",
                "span": get_span(note, "degenerative disc disease"),
                "icd_code": "M51.36",
            },
            {
                "name_as_written": "Schmorl's nodes",
                "normalised_name": "schmorl's nodes",
                "status": "active",
                "span": get_span(note, "Schmorl's nodes"),
                "icd_code": "M51.46",
            },
            {
                "name_as_written": "psoriasis",
                "normalised_name": "psoriasis",
                "status": "active",
                "span": get_span(note, "psoriasis"),
                "icd_code": "L40.9",
            },
            {
                "name_as_written": "compression fractures",
                "normalised_name": "compression fracture",
                "status": "active",
                "span": get_span(note, "compression fractures"),
                "icd_code": "S22.009A",
            },
            {
                "name_as_written": "thoracic spine pain",
                "normalised_name": "thoracic spine pain",
                "status": "active",
                "span": get_span(note, "thoracic spine pain"),
                "icd_code": "M54.6",
            },
        ],
        "medications": [
            {
                "name": "ibuprofen",
                "dose": None,
                "route": "PO",
                "frequency": "occasional",
                "status": "current",
                "span": get_span(note, "ibuprofen"),
            },
            {
                "name": "hydrocodone/acetaminophen",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "discontinued",
                "span": get_span(note, "hydrocodone/acetaminophen"),
            },
            {
                "name": "Motrin",
                "dose": "800 mg",
                "route": "PO",
                "frequency": None,
                "status": "discontinued",
                "span": get_span(note, "Motrin 800 mg"),
            },
        ],
        "procedures": [
            {
                "name": "x-ray of the whole spine",
                "date": "October 4, 2000",
                "span": get_span(note, "x-ray of the whole spine"),
            },
            {
                "name": "MRI",
                "date": None,
                "span": get_span(note, "MRI"),
            },
            {
                "name": "thoracic spine x-rays",
                "date": "October 4, 2000",
                "span": get_span(note, "thoracic spine x-rays"),
            },
            {
                "name": "bone scan",
                "date": None,
                "span": get_span(note, "bone scan"),
            },
            {
                "name": "chiropractic manipulation",
                "date": "December 11, 2000",
                "span": get_span(note, "chiropractic manipulation"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 033 — Consult - History and Phy.
# ============================================================
def build_note_033():
    note = (DATA_DIR / "note_033.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_033",
        "specialty": "Consult - History and Phy.",
        "source_row_index": 4156,
        "diagnoses": [
            {
                "name_as_written": "depression",
                "normalised_name": "depression",
                "status": "active",
                "span": get_span(note, "depression"),
                "icd_code": "F32.9",
            },
            {
                "name_as_written": "ADD",
                "normalised_name": "attention deficit disorder",
                "status": "historical",
                "span": get_span(note, "ADD"),
                "icd_code": "F90.9",
            },
            {
                "name_as_written": "substance abuse",
                "normalised_name": "substance abuse",
                "status": "suspected",
                "span": get_span(note, "substance abuse"),
                "icd_code": "F19.10",
            },
        ],
        "medications": [
            {
                "name": "Celexa",
                "dose": "40 mg",
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Celexa 40 mg"),
            }
        ],
        "procedures": [],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 034 — Cosmetic / Plastic Surgery
# ============================================================
def build_note_034():
    note = (DATA_DIR / "note_034.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_034",
        "specialty": "Cosmetic / Plastic Surgery",
        "source_row_index": 4068,
        "diagnoses": [
            {
                "name_as_written": "Bilateral mammary hypertrophy",
                "normalised_name": "bilateral mammary hypertrophy",
                "status": "active",
                "span": get_span(note, "Bilateral mammary hypertrophy"),
                "icd_code": "N62",
            },
            {
                "name_as_written": "breast asymmetry",
                "normalised_name": "breast asymmetry",
                "status": "active",
                "span": get_span(note, "breast asymmetry"),
                "icd_code": "N64.89",
            },
        ],
        "medications": [
            {
                "name": "bacitracin",
                "dose": None,
                "route": "topical",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "bacitracin"),
            },
            {
                "name": "Dermabond",
                "dose": None,
                "route": "topical",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Dermabond"),
            },
        ],
        "procedures": [
            {
                "name": "Bilateral reduction mammoplasty",
                "date": None,
                "span": get_span(note, "Bilateral reduction mammoplasty"),
            },
            {
                "name": "Jackson-Pratt drain",
                "date": None,
                "span": get_span(note, "Jackson-Pratt drain"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 035 — Dentistry
# ============================================================
def build_note_035():
    note = (DATA_DIR / "note_035.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_035",
        "specialty": "Dentistry",
        "source_row_index": 14,
        "diagnoses": [
            {
                "name_as_written": "Completely bony impacted teeth #1, #16, #17, and #32.",
                "normalised_name": "impacted teeth",
                "status": "active",
                "span": get_span(note, "Completely bony impacted teeth #1, #16, #17, and #32."),
                "icd_code": "K01.1",
            }
        ],
        "medications": [
            {
                "name": "lidocaine",
                "dose": "7.2 mL of lidocaine 2%",
                "route": "local",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "lidocaine"),
            },
            {
                "name": "epinephrine",
                "dose": "1:100,000",
                "route": "local",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "epinephrine"),
            },
            {
                "name": "bupivacaine",
                "dose": "3.6 mL of bupivacaine 0.5%",
                "route": "local",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "bupivacaine"),
            },
        ],
        "procedures": [
            {
                "name": "Surgical removal of completely bony impacted teeth #1, #16, #17, and #32.",
                "date": None,
                "span": get_span(note, "Surgical removal of completely bony impacted teeth #1, #16, #17, and #32."),
            }
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 036 — Dermatology
# ============================================================
def build_note_036():
    note = (DATA_DIR / "note_036.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_036",
        "specialty": "Dermatology",
        "source_row_index": 4015,
        "diagnoses": [
            {
                "name_as_written": "Enlarging nevus of the left upper cheek.",
                "normalised_name": "nevus of left upper cheek",
                "status": "active",
                "span": get_span(note, "Enlarging nevus of the left upper cheek."),
                "icd_code": "D22.39",
            },
            {
                "name_as_written": "Enlarging nevus 0.5 x 1 cm, left lower cheek.",
                "normalised_name": "nevus of left lower cheek",
                "status": "active",
                "span": get_span(note, "Enlarging nevus 0.5 x 1 cm, left lower cheek."),
                "icd_code": "D22.39",
            },
            {
                "name_as_written": "Enlarging superficial nevus 0.5 x 1 cm, right nasal ala.",
                "normalised_name": "superficial nevus of right nasal ala",
                "status": "active",
                "span": get_span(note, "Enlarging superficial nevus 0.5 x 1 cm, right nasal ala."),
                "icd_code": "D22.39",
            },
        ],
        "medications": [
            {
                "name": "lidocaine",
                "dose": "5 mL of 1%",
                "route": "local",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "lidocaine"),
            },
            {
                "name": "epinephrine",
                "dose": "1:100,000",
                "route": "local",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "epinephrine"),
            },
        ],
        "procedures": [
            {
                "name": "Excision of left upper cheek skin neoplasm 0.5 x 1 cm with two layer closure.",
                "date": None,
                "span": get_span(note, "Excision of left upper cheek skin neoplasm 0.5 x 1 cm with two layer closure."),
            },
            {
                "name": "Excision of the left lower cheek skin neoplasm 0.5 x 1 cm with a two layer plastic closure.",
                "date": None,
                "span": get_span(note, "Excision of the left lower cheek skin neoplasm 0.5 x 1 cm with a two layer plastic closure."),
            },
            {
                "name": "Shave excision of the right nasal ala 0.5 x 1 cm skin neoplasm.",
                "date": None,
                "span": get_span(note, "Shave excision of the right nasal ala 0.5 x 1 cm skin neoplasm."),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 037 — Diets and Nutritions
# ============================================================
def build_note_037():
    note = (DATA_DIR / "note_037.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_037",
        "specialty": "Diets and Nutritions",
        "source_row_index": 3988,
        "diagnoses": [
            {
                "name_as_written": "hyperlipidemia",
                "normalised_name": "hyperlipidemia",
                "status": "active",
                "span": get_span(note, "hyperlipidemia"),
                "icd_code": "E78.5",
            },
            {
                "name_as_written": "hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "gastroesophageal reflux disease",
                "normalised_name": "gastroesophageal reflux disease",
                "status": "active",
                "span": get_span(note, "gastroesophageal reflux disease"),
                "icd_code": "K21.9",
            },
        ],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [
            {
                "name": "Height",
                "value": "5 feet 4 inches",
                "unit": None,
                "span": get_span(note, "5 feet 4 inches"),
            },
            {
                "name": "Weight",
                "value": "170",
                "unit": "pounds",
                "span": get_span(note, "170 pounds"),
            },
            {
                "name": "BMI",
                "value": "29",
                "unit": None,
                "span": get_span(note, "BMI is approximately 29"),
            },
        ],
    }


# ============================================================
# NOTE 038 — Discharge Summary
# ============================================================
def build_note_038():
    note = (DATA_DIR / "note_038.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_038",
        "specialty": "Discharge Summary",
        "source_row_index": 3943,
        "diagnoses": [
            {
                "name_as_written": "Right pleural mass",
                "normalised_name": "pleural mass",
                "status": "active",
                "span": get_span(note, "Right pleural mass"),
                "icd_code": "R22.2",
            },
            {
                "name_as_written": "Mesothelioma",
                "normalised_name": "mesothelioma",
                "status": "active",
                "span": get_span(note, "Mesothelioma"),
                "icd_code": "C45.0",
            },
        ],
        "medications": [
            {
                "name": "oxygen",
                "dose": None,
                "route": "inhalation",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "oxygen"),
            },
            {
                "name": "albuterol",
                "dose": None,
                "route": "nebulizer",
                "frequency": "q.i.d.",
                "status": "newly_prescribed",
                "span": get_span(note, "albuterol"),
            },
            {
                "name": "Vicodin",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Vicodin"),
            },
        ],
        "procedures": [
            {
                "name": "Flexible bronchoscopy",
                "date": None,
                "span": get_span(note, "Flexible bronchoscopy"),
            },
            {
                "name": "Mediastinoscopy",
                "date": None,
                "span": get_span(note, "Mediastinoscopy"),
            },
            {
                "name": "Right thoracotomy",
                "date": None,
                "span": get_span(note, "Right thoracotomy"),
            },
            {
                "name": "Parietal pleural biopsy",
                "date": None,
                "span": get_span(note, "Parietal pleural biopsy"),
            },
            {
                "name": "chest x-ray",
                "date": None,
                "span": get_span(note, "chest x-ray"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 039 — ENT - Otolaryngology
# ============================================================
def build_note_039():
    note = (DATA_DIR / "note_039.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_039",
        "specialty": "ENT - Otolaryngology",
        "source_row_index": 3724,
        "diagnoses": [
            {
                "name_as_written": "parathyroid hyperplasia",
                "normalised_name": "parathyroid hyperplasia",
                "status": "active",
                "span": get_span(note, "parathyroid hyperplasia"),
                "icd_code": "E21.0",
            }
        ],
        "medications": [
            {
                "name": "Tums",
                "dose": "three Tums",
                "route": "orally",
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "Tums"),
            },
            {
                "name": "heparin",
                "dose": None,
                "route": "IV",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "heparin"),
            },
            {
                "name": "prednisone",
                "dose": "double her regular dose",
                "route": "orally",
                "frequency": "for the next five days",
                "status": "current",
                "span": get_span(note, "prednisone"),
            },
            {
                "name": "Lortab Elixir",
                "dose": "2 to 4 teaspoons",
                "route": "orally",
                "frequency": "every four hours p.r.n.",
                "status": "newly_prescribed",
                "span": get_span(note, "Lortab Elixir"),
            },
            {
                "name": "calcium",
                "dose": None,
                "route": "orally",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "calcium dosage"),
            },
        ],
        "procedures": [
            {
                "name": "open parathyroid exploration",
                "date": None,
                "span": get_span(note, "open parathyroid exploration"),
            },
            {
                "name": "subtotal parathyroidectomy",
                "date": None,
                "span": get_span(note, "subtotal parathyroidectomy"),
            },
            {
                "name": "intraoperative PTH monitoring",
                "date": None,
                "span": get_span(note, "intraoperative PTH monitoring"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "calcium",
                "value": "7.5",
                "unit": "mg/dL",
                "span": get_span(note, "7.5"),
            }
        ],
    }


# ============================================================
# NOTE 040 — Emergency Room Reports
# ============================================================
def build_note_040():
    note = (DATA_DIR / "note_040.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_040",
        "specialty": "Emergency Room Reports",
        "source_row_index": 3875,
        "diagnoses": [
            {
                "name_as_written": "alcohol abuse",
                "normalised_name": "alcohol abuse",
                "status": "active",
                "span": get_span(note, "alcohol abuse"),
                "icd_code": "F10.10",
            },
            {
                "name_as_written": "right hip fracture",
                "normalised_name": "hip fracture",
                "status": "historical",
                "span": get_span(note, "right hip fracture"),
                "icd_code": "S72.91XA",
            },
            {
                "name_as_written": "hyponatremia",
                "normalised_name": "hyponatremia",
                "status": "active",
                "span": get_span(note, "hyponatremia"),
                "icd_code": "E87.1",
            },
        ],
        "medications": [
            {
                "name": "Ativan",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Ativan"),
            }
        ],
        "procedures": [
            {
                "name": "chest x-ray",
                "date": None,
                "span": get_span(note, "chest x-ray"),
            },
            {
                "name": "appendectomy",
                "date": None,
                "span": get_span(note, "appendectomy"),
            },
            {
                "name": "TAH/BSO",
                "date": None,
                "span": get_span(note, "TAH/BSO"),
            },
            {
                "name": "CT scan",
                "date": None,
                "span": get_span(note, "CT scan"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "Temp",
                "value": "98.3",
                "unit": "°F",
                "span": get_span(note, "Temp 98.3"),
            },
            {
                "name": "HR",
                "value": "82",
                "unit": "bpm",
                "span": get_span(note, "heart rate 82"),
            },
            {
                "name": "RR",
                "value": "24",
                "unit": "breaths/min",
                "span": get_span(note, "respiratory rate 24"),
            },
            {
                "name": "BP",
                "value": "141/70",
                "unit": "mmHg",
                "span": get_span(note, "blood pressure 141/70"),
            },
            {
                "name": "Sodium",
                "value": "107",
                "unit": "mEq/L",
                "span": get_span(note, "Sodium is 107"),
            },
            {
                "name": "chloride",
                "value": "68",
                "unit": "mEq/L",
                "span": get_span(note, "68 chloride"),
            },
            {
                "name": "potassium",
                "value": "2.8",
                "unit": "mEq/L",
                "span": get_span(note, "potassium of 2.8"),
            },
        ],
    }


# ============================================================
# NOTE 041 — Endocrinology
# ============================================================
def build_note_041():
    note = (DATA_DIR / "note_041.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_041",
        "specialty": "Endocrinology",
        "source_row_index": 3788,
        "diagnoses": [
            {
                "name_as_written": "Ventilator-dependent respiratory failure",
                "normalised_name": "ventilator-dependent respiratory failure",
                "status": "active",
                "span": get_span(note, "Ventilator-dependent respiratory failure"),
                "icd_code": "J96.00",
            },
            {
                "name_as_written": "Multiple strokes",
                "normalised_name": "stroke",
                "status": "active",
                "span": get_span(note, "Multiple strokes"),
                "icd_code": "I63.9",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Tracheostomy",
                "date": None,
                "span": get_span(note, "Tracheostomy"),
            },
            {
                "name": "Thyroid isthmusectomy",
                "date": None,
                "span": get_span(note, "Thyroid isthmusectomy"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 042 — Gastroenterology (CT abdomen/pelvis radiology report)
# ============================================================
def build_note_042():
    note = (DATA_DIR / "note_042.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_042",
        "specialty": "Gastroenterology",
        "source_row_index": 3601,
        "diagnoses": [
            {
                "name_as_written": "hypodense mass in the cervix and lower uterine segment",
                "normalised_name": "cervical and lower uterine segment mass",
                "status": "active",
                "span": get_span(note, "hypodense mass in the cervix and lower uterine segment"),
                "icd_code": "N88.8",
            },
            {
                "name_as_written": "intramural hypodense mass involving the dorsal uterine fundus",
                "normalised_name": "uterine fibroid",
                "status": "suspected",
                "span": get_span(note, "intramural hypodense mass involving the dorsal uterine fundus"),
                "icd_code": "D25.1",
            },
            {
                "name_as_written": "diverticula",
                "normalised_name": "diverticula of colon",
                "status": "active",
                "span": get_span(note, "diverticula"),
                "icd_code": "K57.30",
            },
            {
                "name_as_written": "diverticulitis",
                "normalised_name": "diverticulitis",
                "status": "ruled_out",
                "span": get_span(note, "diverticulitis"),
                "icd_code": "K57.32",
            },
            {
                "name_as_written": "calcified granulomas",
                "normalised_name": "calcified granulomas of spleen",
                "status": "active",
                "span": get_span(note, "calcified granulomas"),
                "icd_code": "D86.9",
            },
            {
                "name_as_written": "mild facet degenerative changes",
                "normalised_name": "facet arthropathy",
                "status": "active",
                "span": get_span(note, "mild facet degenerative changes"),
                "icd_code": "M47.817",
            },
        ],
        "medications": [
            {
                "name": "Isovue-300",
                "dose": "100 mL",
                "route": "intravenous",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Isovue-300"),
            }
        ],
        "procedures": [
            {
                "name": "CT examination of the abdomen and pelvis",
                "date": None,
                "span": get_span(note, "CT examination of the abdomen and pelvis"),
            }
        ],
        "allergies": [],
        "vitals": [],
    }


def main():
    builders = [
        build_note_028,
        build_note_029,
        build_note_030,
        build_note_031,
        build_note_032,
        build_note_033,
        build_note_034,
        build_note_035,
        build_note_036,
        build_note_037,
        build_note_038,
        build_note_039,
        build_note_040,
        build_note_041,
        build_note_042,
    ]

    all_ok = True
    for builder in builders:
        data = builder()
        ok = write_and_verify(data["note_id"], data)
        if not ok:
            all_ok = False

    print("\nRunning verify_gold.py on all gold files...")
    res = subprocess.run(["python", "src/utils/verify_gold.py"], capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr)
    if res.returncode != 0:
        print("verify_gold.py FAILED!")
        all_ok = False
    else:
        print("verify_gold.py PASSED!")

    return all_ok


if __name__ == "__main__":
    main()
