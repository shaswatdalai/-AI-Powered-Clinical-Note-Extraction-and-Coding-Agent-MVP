"""
Build gold/note_073.json through gold/note_086.json.
Run from project root: python scripts/build_gold_073_086.py
"""
import json
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
    meta_path = DATA_DIR / f"{note_id}.meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))

    assert data["note_id"] == note_id, f"note_id mismatch: {data['note_id']} vs {note_id}"
    assert data["specialty"] == meta["specialty"].strip(), f"specialty mismatch: {data['specialty']!r} vs {meta['specialty'].strip()!r}"
    assert data["source_row_index"] == meta["original_index"], f"source_row_index mismatch"

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
# NOTE 073 — General Medicine
# ============================================================
def build_note_073():
    note = (DATA_DIR / "note_073.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_073",
        "specialty": "General Medicine",
        "source_row_index": 3328,
        "diagnoses": [
            {
                "name_as_written": "acute pancreatitis",
                "normalised_name": "acute pancreatitis",
                "status": "active",
                "span": get_span(note, "acute pancreatitis"),
                "icd_code": "K85.90",
            },
            {
                "name_as_written": "dementia of Alzheimer type",
                "normalised_name": "alzheimer dementia",
                "status": "active",
                "span": get_span(note, "dementia of Alzheimer type"),
                "icd_code": "G30.9",
            },
            {
                "name_as_written": "anxiety",
                "normalised_name": "anxiety",
                "status": "active",
                "span": get_span(note, "anxiety"),
                "icd_code": "F41.9",
            },
            {
                "name_as_written": "osteoarthritis",
                "normalised_name": "osteoarthritis",
                "status": "active",
                "span": get_span(note, "osteoarthritis"),
                "icd_code": "M19.90",
            },
            {
                "name_as_written": "hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "Leukocytosis",
                "normalised_name": "leukocytosis",
                "status": "active",
                "span": get_span(note, "Leukocytosis"),
                "icd_code": "D72.829",
            },
            {
                "name_as_written": "Urinary tract infection",
                "normalised_name": "urinary tract infection",
                "status": "active",
                "span": get_span(note, "Urinary tract infection"),
                "icd_code": "N39.0",
            },
            {
                "name_as_written": "Hyponatremia",
                "normalised_name": "hyponatremia",
                "status": "active",
                "span": get_span(note, "Hyponatremia"),
                "icd_code": "E87.1",
            },
            {
                "name_as_written": "cardiomegaly",
                "normalised_name": "cardiomegaly",
                "status": "active",
                "span": get_span(note, "cardiomegaly"),
                "icd_code": "I51.7",
            },
            {
                "name_as_written": "atelectasis",
                "normalised_name": "atelectasis",
                "status": "active",
                "span": get_span(note, "atelectasis"),
                "icd_code": "J98.11",
            },
            {
                "name_as_written": "fatty infiltration",
                "normalised_name": "fatty liver",
                "status": "active",
                "span": get_span(note, "fatty infiltration"),
                "icd_code": "K76.0",
            },
        ],
        "medications": [
            {
                "name": "alprazolam",
                "dose": "0.5 mg",
                "route": None,
                "frequency": "b.i.d. p.r.n.",
                "status": "current",
                "span": get_span(note, "alprazolam"),
            },
            {
                "name": "mirtazapine",
                "dose": "30 mg",
                "route": "p.o.",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "mirtazapine"),
            },
            {
                "name": "Aricept",
                "dose": "10 mg",
                "route": "p.o.",
                "frequency": "nightly",
                "status": "current",
                "span": get_span(note, "Aricept"),
            },
            {
                "name": "Namenda",
                "dose": "10 mg",
                "route": "p.o.",
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "Namenda"),
            },
            {
                "name": "Benicar",
                "dose": "40 mg",
                "route": "p.o.",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Benicar"),
            },
            {
                "name": "Claritin",
                "dose": "10 mg",
                "route": None,
                "frequency": "daily p.r.n.",
                "status": "current",
                "span": get_span(note, "Claritin"),
            },
            {
                "name": "antibiotics",
                "dose": None,
                "route": "IV",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "IV antibiotics"),
            },
            {
                "name": "Zofran",
                "dose": None,
                "route": "IV",
                "frequency": "p.r.n.",
                "status": "newly_prescribed",
                "span": get_span(note, "Zofran"),
            },
        ],
        "procedures": [
            {
                "name": "X-ray of abdomen",
                "date": None,
                "span": get_span(note, "X-ray of abdomen"),
            },
            {
                "name": "CT of the abdomen",
                "date": None,
                "span": get_span(note, "CT of the abdomen"),
            },
            {
                "name": "Ultrasound of the abdomen",
                "date": None,
                "span": get_span(note, "Ultrasound of the abdomen"),
            },
            {
                "name": "EKG",
                "date": None,
                "span": get_span(note, "EKG"),
            },
        ],
        "allergies": [
            {
                "substance": "POLLENS",
                "reaction": None,
                "span": get_span(note, "POLLENS"),
            }
        ],
        "vitals": [
            {
                "name": "Temperature",
                "value": "99.5",
                "unit": "°F",
                "span": get_span(note, "Temperature of 99.5"),
            },
            {
                "name": "pulse",
                "value": "82",
                "unit": "bpm",
                "span": get_span(note, "pulse 82"),
            },
            {
                "name": "respirations",
                "value": "18",
                "unit": "breaths/min",
                "span": get_span(note, "respirations 18"),
            },
            {
                "name": "blood pressure",
                "value": "150/68",
                "unit": "mmHg",
                "span": get_span(note, "150/68"),
            },
            {
                "name": "pulse ox",
                "value": "90%",
                "unit": "%",
                "span": get_span(note, "pulse ox is 90%"),
            },
        ],
    }


# ============================================================
# NOTE 074 — Hematology - Oncology
# ============================================================
def build_note_074():
    note = (DATA_DIR / "note_074.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_074",
        "specialty": "Hematology - Oncology",
        "source_row_index": 3120,
        "diagnoses": [
            {
                "name_as_written": "Posttransplant lymphoproliferative disorder",
                "normalised_name": "posttransplant lymphoproliferative disorder",
                "status": "active",
                "span": get_span(note, "Posttransplant lymphoproliferative disorder"),
                "icd_code": "D47.Z1",
            },
            {
                "name_as_written": "Chronic renal insufficiency",
                "normalised_name": "chronic renal insufficiency",
                "status": "active",
                "span": get_span(note, "Chronic renal insufficiency"),
                "icd_code": "N18.9",
            },
            {
                "name_as_written": "Squamous cell carcinoma of the skin",
                "normalised_name": "squamous cell carcinoma of the skin",
                "status": "active",
                "span": get_span(note, "Squamous cell carcinoma of the skin"),
                "icd_code": "C44.92",
            },
            {
                "name_as_written": "Anemia",
                "normalised_name": "anemia",
                "status": "active",
                "span": get_span(note, "Anemia"),
                "icd_code": "D63.1",
            },
            {
                "name_as_written": "Hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "Hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "large cell lymphoma",
                "normalised_name": "diffuse large b-cell lymphoma",
                "status": "active",
                "span": get_span(note, "large cell lymphoma"),
                "icd_code": "C83.30",
            },
            {
                "name_as_written": "sepsis",
                "normalised_name": "sepsis",
                "status": "historical",
                "span": get_span(note, "sepsis"),
                "icd_code": "A41.9",
            },
            {
                "name_as_written": "Systolic flow murmur",
                "normalised_name": "flow murmur",
                "status": "active",
                "span": get_span(note, "Systolic flow murmur"),
                "icd_code": "R01.0",
            },
        ],
        "medications": [
            {
                "name": "rituximab",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "rituximab"),
            },
            {
                "name": "cyclophosphamide",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "cyclophosphamide"),
            },
            {
                "name": "daunorubicin",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "daunorubicin"),
            },
            {
                "name": "vincristine",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "vincristine"),
            },
            {
                "name": "prednisone",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "prednisone"),
            },
        ],
        "procedures": [
            {
                "name": "lymph node biopsy",
                "date": None,
                "span": get_span(note, "lymph node biopsy"),
            },
            {
                "name": "Chemotherapy",
                "date": None,
                "span": get_span(note, "Chemotherapy"),
            },
            {
                "name": "PET scan",
                "date": None,
                "span": get_span(note, "PET scan"),
            },
            {
                "name": "Renal transplant",
                "date": None,
                "span": get_span(note, "Renal transplant"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "Blood pressure",
                "value": "161/80",
                "unit": "mmHg",
                "span": get_span(note, "161/80"),
            },
            {
                "name": "pulse",
                "value": "65",
                "unit": "bpm",
                "span": get_span(note, "pulse 65"),
            },
            {
                "name": "weight",
                "value": "71.5",
                "unit": "kg",
                "span": get_span(note, "71.5 kg"),
            },
        ],
    }


# ============================================================
# NOTE 075 — Hospice - Palliative Care
# ============================================================
def build_note_075():
    note = (DATA_DIR / "note_075.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_075",
        "specialty": "Hospice - Palliative Care",
        "source_row_index": 3111,
        "diagnoses": [
            {
                "name_as_written": "hyponatremia",
                "normalised_name": "hyponatremia",
                "status": "active",
                "span": get_span(note, "hyponatremia"),
                "icd_code": "E87.1",
            },
            {
                "name_as_written": "aspiration pneumonia",
                "normalised_name": "aspiration pneumonia",
                "status": "active",
                "span": get_span(note, "aspiration pneumonia"),
                "icd_code": "J69.0",
            },
            {
                "name_as_written": "ovarian malignancy",
                "normalised_name": "malignant neoplasm of ovary",
                "status": "suspected",
                "span": get_span(note, "ovarian malignancy"),
                "icd_code": "C56.9",
            },
            {
                "name_as_written": "dysphagia",
                "normalised_name": "dysphagia",
                "status": "active",
                "span": get_span(note, "dysphagia"),
                "icd_code": "R13.10",
            },
            {
                "name_as_written": "hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "tachycardia",
                "normalised_name": "tachycardia",
                "status": "active",
                "span": get_span(note, "tachycardia"),
                "icd_code": "R00.0",
            },
        ],
        "medications": [
            {
                "name": "morphine",
                "dose": None,
                "route": "intravenous",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "morphine"),
            }
        ],
        "procedures": [
            {
                "name": "CPR",
                "date": None,
                "span": get_span(note, "CPR"),
            },
            {
                "name": "intubated",
                "date": None,
                "span": get_span(note, "intubated"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 076 — IME-QME-Work Comp etc.
# ============================================================
def build_note_076():
    note = (DATA_DIR / "note_076.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_076",
        "specialty": "IME-QME-Work Comp etc.",
        "source_row_index": 3107,
        "diagnoses": [
            {
                "name_as_written": "First-degree and second-degree burns",
                "normalised_name": "burn of right forearm",
                "status": "active",
                "span": get_span(note, "First-degree and second-degree burns"),
                "icd_code": "T22.211A",
            }
        ],
        "medications": [
            {
                "name": "Demerol",
                "dose": "50 mg",
                "route": "IM",
                "frequency": None,
                "status": "discontinued",
                "span": get_span(note, "Demerol"),
            },
            {
                "name": "Neosporin",
                "dose": None,
                "route": "topical",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Neosporin"),
            },
            {
                "name": "Tylenol No. 3",
                "dose": "tabs #4",
                "route": None,
                "frequency": "one or two every four hours p.r.n.",
                "status": "newly_prescribed",
                "span": get_span(note, "Tylenol No. 3"),
            },
        ],
        "procedures": [
            {
                "name": "burn dressing",
                "date": None,
                "span": get_span(note, "burn dressing"),
            }
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 077 — Lab Medicine - Pathology
# ============================================================
def build_note_077():
    note = (DATA_DIR / "note_077.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_077",
        "specialty": "Lab Medicine - Pathology",
        "source_row_index": 3083,
        "diagnoses": [
            {
                "name_as_written": "right ovarian cyst",
                "normalised_name": "ovarian cyst",
                "status": "active",
                "span": get_span(note, "right ovarian cyst"),
                "icd_code": "N83.201",
            },
            {
                "name_as_written": "Benign cystic ovary",
                "normalised_name": "benign ovarian cyst",
                "status": "active",
                "span": get_span(note, "Benign cystic ovary"),
                "icd_code": "N83.20",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "frozen section",
                "date": None,
                "span": get_span(note, "frozen section"),
            }
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 078 — Letters
# ============================================================
def build_note_078():
    note = (DATA_DIR / "note_078.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_078",
        "specialty": "Letters",
        "source_row_index": 3073,
        "diagnoses": [
            {
                "name_as_written": "bulbar cerebral palsy",
                "normalised_name": "cerebral palsy",
                "status": "active",
                "span": get_span(note, "bulbar cerebral palsy"),
                "icd_code": "G80.9",
            },
            {
                "name_as_written": "hypotonia",
                "normalised_name": "hypotonia",
                "status": "active",
                "span": get_span(note, "hypotonia"),
                "icd_code": "P94.2",
            },
            {
                "name_as_written": "tonsillar hypertrophy",
                "normalised_name": "tonsillar hypertrophy",
                "status": "active",
                "span": get_span(note, "tonsillar hypertrophy"),
                "icd_code": "J35.1",
            },
            {
                "name_as_written": "chronic allergic rhinitis",
                "normalised_name": "chronic allergic rhinitis",
                "status": "active",
                "span": get_span(note, "chronic allergic rhinitis"),
                "icd_code": "J30.9",
            },
        ],
        "medications": [
            {
                "name": "Flonase",
                "dose": "two sprays to each nostril",
                "route": "nasal",
                "frequency": "once a day",
                "status": "current",
                "span": get_span(note, "Flonase"),
            },
            {
                "name": "Zyrtec",
                "dose": "10 mg",
                "route": None,
                "frequency": "a day",
                "status": "current",
                "span": get_span(note, "Zyrtec"),
            },
        ],
        "procedures": [],
        "allergies": [
            {
                "substance": "penicillin",
                "reaction": None,
                "span": get_span(note, "penicillin"),
            }
        ],
        "vitals": [],
    }


# ============================================================
# NOTE 079 — Nephrology
# ============================================================
def build_note_079():
    note = (DATA_DIR / "note_079.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_079",
        "specialty": "Nephrology",
        "source_row_index": 3054,
        "diagnoses": [
            {
                "name_as_written": "coronary artery disease",
                "normalised_name": "coronary artery disease",
                "status": "active",
                "span": get_span(note, "coronary artery disease"),
                "icd_code": "I25.10",
            },
            {
                "name_as_written": "hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "diabetes",
                "normalised_name": "diabetes mellitus",
                "status": "active",
                "span": get_span(note, "diabetes"),
                "icd_code": "E11.9",
            },
            {
                "name_as_written": "stage III CKD",
                "normalised_name": "chronic kidney disease, stage 3",
                "status": "active",
                "span": get_span(note, "stage III CKD"),
                "icd_code": "N18.30",
            },
            {
                "name_as_written": "acute on chronic kidney failure",
                "normalised_name": "acute on chronic kidney failure",
                "status": "active",
                "span": get_span(note, "acute on chronic kidney failure"),
                "icd_code": "N17.9",
            },
            {
                "name_as_written": "prostatic hypertrophy",
                "normalised_name": "benign prostatic hyperplasia",
                "status": "active",
                "span": get_span(note, "prostatic hypertrophy"),
                "icd_code": "N40.0",
            },
            {
                "name_as_written": "Heart failure",
                "normalised_name": "heart failure",
                "status": "active",
                "span": get_span(note, "Heart failure"),
                "icd_code": "I50.9",
            },
            {
                "name_as_written": "mitral regurgitation",
                "normalised_name": "mitral regurgitation",
                "status": "active",
                "span": get_span(note, "mitral regurgitation"),
                "icd_code": "I34.0",
            },
            {
                "name_as_written": "GI bleed",
                "normalised_name": "gastrointestinal hemorrhage",
                "status": "historical",
                "span": get_span(note, "GI bleed"),
                "icd_code": "K92.2",
            },
            {
                "name_as_written": "Hyperlipidemia",
                "normalised_name": "hyperlipidemia",
                "status": "active",
                "span": get_span(note, "Hyperlipidemia"),
                "icd_code": "E78.5",
            },
            {
                "name_as_written": "Sleep apnea",
                "normalised_name": "sleep apnea",
                "status": "active",
                "span": get_span(note, "Sleep apnea"),
                "icd_code": "G47.30",
            },
            {
                "name_as_written": "Orthostatic hypotension",
                "normalised_name": "orthostatic hypotension",
                "status": "active",
                "span": get_span(note, "Orthostatic hypotension"),
                "icd_code": "I95.1",
            },
            {
                "name_as_written": "myositis",
                "normalised_name": "myositis",
                "status": "suspected",
                "span": get_span(note, "myositis"),
                "icd_code": "M60.9",
            },
        ],
        "medications": [
            {
                "name": "Imdur",
                "dose": "20 mg",
                "route": None,
                "frequency": "two to three times daily",
                "status": "current",
                "span": get_span(note, "Imdur"),
            },
            {
                "name": "nitroglycerin",
                "dose": None,
                "route": None,
                "frequency": "p.r.n.",
                "status": "current",
                "span": get_span(note, "nitroglycerin"),
            },
            {
                "name": "insulin 70/30",
                "dose": "40/45 units",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "insulin 70/30"),
            },
            {
                "name": "Zetia",
                "dose": "10 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Zetia"),
            },
            {
                "name": "Prevacid",
                "dose": "30 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Prevacid"),
            },
            {
                "name": "Plavix",
                "dose": "75 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Plavix"),
            },
            {
                "name": "potassium",
                "dose": "10 mEq",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "potassium"),
            },
            {
                "name": "Lasix",
                "dose": "60 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Lasix"),
            },
            {
                "name": "folate",
                "dose": "1 mg",
                "route": None,
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "folate"),
            },
            {
                "name": "Niaspan",
                "dose": "500 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Niaspan"),
            },
            {
                "name": "atenolol",
                "dose": "50 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "atenolol"),
            },
            {
                "name": "enalapril",
                "dose": "10 mg",
                "route": None,
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "enalapril"),
            },
            {
                "name": "glyburide",
                "dose": "10 mg",
                "route": None,
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "glyburide"),
            },
            {
                "name": "Xanax",
                "dose": "0.25 mg",
                "route": None,
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "Xanax"),
            },
            {
                "name": "aspirin",
                "dose": "325 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "aspirin"),
            },
            {
                "name": "Tylenol",
                "dose": None,
                "route": None,
                "frequency": "p.r.n.",
                "status": "current",
                "span": get_span(note, "Tylenol"),
            },
            {
                "name": "Zantac",
                "dose": "150 mg",
                "route": None,
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "Zantac"),
            },
            {
                "name": "Crestor",
                "dose": "5 mg",
                "route": None,
                "frequency": "daily",
                "status": "discontinued",
                "span": get_span(note, "Crestor"),
            },
            {
                "name": "TriCor",
                "dose": "145 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "TriCor"),
            },
            {
                "name": "Digitek",
                "dose": "0.125 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Digitek"),
            },
            {
                "name": "Celexa",
                "dose": "20 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Celexa"),
            },
            {
                "name": "Flomax",
                "dose": "0.4 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Flomax"),
            },
        ],
        "procedures": [
            {
                "name": "CABG",
                "date": "December 2001",
                "span": get_span(note, "CABG"),
            },
            {
                "name": "laser surgery",
                "date": None,
                "span": get_span(note, "laser surgery"),
            },
            {
                "name": "Back surgery",
                "date": None,
                "span": get_span(note, "Back surgery"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "Pulse",
                "value": "78",
                "unit": "bpm",
                "span": get_span(note, "Pulse 78"),
            },
            {
                "name": "Blood pressure",
                "value": "116/60",
                "unit": "mmHg",
                "span": get_span(note, "116/60"),
            },
            {
                "name": "Height",
                "value": "5'7\"",
                "unit": None,
                "span": get_span(note, "5'7\""),
            },
            {
                "name": "Weight",
                "value": "78.6",
                "unit": "kg",
                "span": get_span(note, "78.6 kg"),
            },
        ],
    }


# ============================================================
# NOTE 080 — Neurology
# ============================================================
def build_note_080():
    note = (DATA_DIR / "note_080.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_080",
        "specialty": "Neurology",
        "source_row_index": 2972,
        "diagnoses": [
            {
                "name_as_written": "anaplastic astrocytoma",
                "normalised_name": "anaplastic astrocytoma",
                "status": "active",
                "span": get_span(note, "anaplastic astrocytoma"),
                "icd_code": "C71.2",
            },
            {
                "name_as_written": "right facial droop",
                "normalised_name": "facial droop",
                "status": "active",
                "span": get_span(note, "right facial droop"),
                "icd_code": "R29.810",
            },
        ],
        "medications": [
            {
                "name": "Temodar",
                "dose": "75 mg/sq m",
                "route": None,
                "frequency": "everyday for 21 days out of 28 days",
                "status": "newly_prescribed",
                "span": get_span(note, "Temodar"),
            },
            {
                "name": "thalidomide",
                "dose": "100 mg/day",
                "route": None,
                "frequency": None,
                "status": "discontinued",
                "span": get_span(note, "thalidomide"),
            },
        ],
        "procedures": [
            {
                "name": "MRI",
                "date": None,
                "span": get_span(note, "MRI"),
            },
            {
                "name": "radiation",
                "date": None,
                "span": get_span(note, "radiation"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 081 — Neurosurgery
# ============================================================
def build_note_081():
    note = (DATA_DIR / "note_081.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_081",
        "specialty": "Neurosurgery",
        "source_row_index": 2701,
        "diagnoses": [
            {
                "name_as_written": "Severe lumbar spondylosis",
                "normalised_name": "lumbar spondylosis",
                "status": "active",
                "span": get_span(note, "Severe lumbar spondylosis"),
                "icd_code": "M47.816",
            },
            {
                "name_as_written": "herniated disk",
                "normalised_name": "lumbar disc herniation",
                "status": "active",
                "span": get_span(note, "herniated disk"),
                "icd_code": "M51.26",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Revision laminectomy L5-S1",
                "date": None,
                "span": get_span(note, "Revision laminectomy L5-S1"),
            },
            {
                "name": "discectomy L5-S1",
                "date": None,
                "span": get_span(note, "discectomy L5-S1"),
            },
            {
                "name": "right medial facetectomy",
                "date": None,
                "span": get_span(note, "right medial facetectomy"),
            },
            {
                "name": "arthrodesis",
                "date": None,
                "span": get_span(note, "arthrodesis"),
            },
            {
                "name": "endotracheal tube intubation",
                "date": None,
                "span": get_span(note, "endotracheal tube intubation"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 082 — Obstetrics / Gynecology
# ============================================================
def build_note_082():
    note = (DATA_DIR / "note_082.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_082",
        "specialty": "Obstetrics / Gynecology",
        "source_row_index": 2642,
        "diagnoses": [
            {
                "name_as_written": "Abnormal uterine bleeding",
                "normalised_name": "abnormal uterine bleeding",
                "status": "active",
                "span": get_span(note, "Abnormal uterine bleeding"),
                "icd_code": "N93.9",
            },
            {
                "name_as_written": "retained products",
                "normalised_name": "retained products of conception",
                "status": "ruled_out",
                "span": get_span(note, "retained products"),
                "icd_code": "O03.4",
            },
            {
                "name_as_written": "endometrial polyps",
                "normalised_name": "endometrial polyp",
                "status": "ruled_out",
                "span": get_span(note, "endometrial polyps"),
                "icd_code": "N84.0",
            },
            {
                "name_as_written": "hyperplastic",
                "normalised_name": "endometrial hyperplasia",
                "status": "active",
                "span": get_span(note, "hyperplastic"),
                "icd_code": "N85.00",
            },
            {
                "name_as_written": "endometrial perforation",
                "normalised_name": "uterine perforation",
                "status": "suspected",
                "span": get_span(note, "endometrial perforation"),
                "icd_code": "N99.820",
            },
        ],
        "medications": [
            {
                "name": "Tylenol #3",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Tylenol #3"),
            }
        ],
        "procedures": [
            {
                "name": "Dilation and curettage",
                "date": None,
                "span": get_span(note, "Dilation and curettage"),
            },
            {
                "name": "Hysteroscopy",
                "date": None,
                "span": get_span(note, "Hysteroscopy"),
            },
            {
                "name": "spontaneous vaginal delivery",
                "date": "7 months",
                "span": get_span(note, "spontaneous vaginal delivery"),
            },
            {
                "name": "ultrasound",
                "date": None,
                "span": get_span(note, "ultrasound"),
            },
        ],
        "allergies": [
            {
                "substance": "Motrin",
                "reaction": None,
                "span": get_span(note, "Motrin"),
            }
        ],
        "vitals": [],
    }


# ============================================================
# NOTE 083 — Office Notes
# ============================================================
def build_note_083():
    note = (DATA_DIR / "note_083.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_083",
        "specialty": "Office Notes",
        "source_row_index": 2483,
        "diagnoses": [
            {
                "name_as_written": "chronic kidney disease",
                "normalised_name": "chronic kidney disease",
                "status": "active",
                "span": get_span(note, "chronic kidney disease"),
                "icd_code": "N18.9",
            },
            {
                "name_as_written": "nephrosclerosis",
                "normalised_name": "nephrosclerosis",
                "status": "active",
                "span": get_span(note, "nephrosclerosis"),
                "icd_code": "I12.9",
            },
            {
                "name_as_written": "nonfunctioning right kidney",
                "normalised_name": "nonfunctioning kidney",
                "status": "active",
                "span": get_span(note, "nonfunctioning right kidney"),
                "icd_code": "N28.89",
            },
            {
                "name_as_written": "hematuria",
                "normalised_name": "hematuria",
                "status": "ruled_out",
                "span": get_span(note, "hematuria"),
                "icd_code": "R31.9",
            },
            {
                "name_as_written": "stage III chronic kidney disease",
                "normalised_name": "chronic kidney disease, stage 3",
                "status": "active",
                "span": get_span(note, "stage III chronic kidney disease"),
                "icd_code": "N18.30",
            },
        ],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 084 — Ophthalmology
# ============================================================
def build_note_084():
    note = (DATA_DIR / "note_084.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_084",
        "specialty": "Ophthalmology",
        "source_row_index": 2408,
        "diagnoses": [
            {
                "name_as_written": "Cataract",
                "normalised_name": "cataract",
                "status": "active",
                "span": get_span(note, "Cataract"),
                "icd_code": "H26.9",
            }
        ],
        "medications": [
            {
                "name": "Maxitrol",
                "dose": None,
                "route": "ophthalmic",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Maxitrol"),
            }
        ],
        "procedures": [
            {
                "name": "Cataract extraction via phacoemulsification with posterior chamber intraocular lens implantation",
                "date": None,
                "span": get_span(note, "Cataract extraction via phacoemulsification with posterior chamber intraocular lens implantation"),
            },
            {
                "name": "Paracentesis",
                "date": None,
                "span": get_span(note, "Paracentesis"),
            },
            {
                "name": "capsulorrhexis",
                "date": None,
                "span": get_span(note, "capsulorrhexis"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 085 — Orthopedic
# ============================================================
def build_note_085():
    note = (DATA_DIR / "note_085.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_085",
        "specialty": "Orthopedic",
        "source_row_index": 2277,
        "diagnoses": [
            {
                "name_as_written": "osteochondritis dissecans",
                "normalised_name": "osteochondritis dissecans of knee",
                "status": "active",
                "span": get_span(note, "osteochondritis dissecans"),
                "icd_code": "M93.262",
            },
            {
                "name_as_written": "loose body",
                "normalised_name": "loose body in knee joint",
                "status": "active",
                "span": get_span(note, "loose body"),
                "icd_code": "M23.42",
            },
            {
                "name_as_written": "synovitis",
                "normalised_name": "synovitis of knee",
                "status": "active",
                "span": get_span(note, "synovitis"),
                "icd_code": "M65.9",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Left knee arthroscopy",
                "date": None,
                "span": get_span(note, "Left knee arthroscopy"),
            },
            {
                "name": "microfracture of the medial femoral condyle",
                "date": None,
                "span": get_span(note, "microfracture of the medial femoral condyle"),
            },
            {
                "name": "chondroplasty",
                "date": None,
                "span": get_span(note, "chondroplasty"),
            },
            {
                "name": "MRI",
                "date": None,
                "span": get_span(note, "MRI"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 086 — Pain Management
# ============================================================
def build_note_086():
    note = (DATA_DIR / "note_086.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_086",
        "specialty": "Pain Management",
        "source_row_index": 2006,
        "diagnoses": [],
        "medications": [],
        "procedures": [
            {
                "name": "Cervical epidural steroid injection C7-T1",
                "date": None,
                "span": get_span(note, "Cervical epidural steroid injection C7-T1"),
            },
            {
                "name": "EKG",
                "date": None,
                "span": get_span(note, "EKG"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


def main():
    builders = [
        ("note_073", build_note_073),
        ("note_074", build_note_074),
        ("note_075", build_note_075),
        ("note_076", build_note_076),
        ("note_077", build_note_077),
        ("note_078", build_note_078),
        ("note_079", build_note_079),
        ("note_080", build_note_080),
        ("note_081", build_note_081),
        ("note_082", build_note_082),
        ("note_083", build_note_083),
        ("note_084", build_note_084),
        ("note_085", build_note_085),
        ("note_086", build_note_086),
    ]

    all_passed = True
    for note_id, builder in builders:
        data = builder()
        ok = write_and_verify(note_id, data)
        if not ok:
            all_passed = False

    if all_passed:
        print("\nAll 14 notes (073-086) built and verified successfully!")
    else:
        print("\nSome notes had errors!")


if __name__ == "__main__":
    main()
