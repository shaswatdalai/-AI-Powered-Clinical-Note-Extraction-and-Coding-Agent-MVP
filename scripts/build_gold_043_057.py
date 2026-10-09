"""
Build gold/note_043.json through gold/note_057.json.
Run from project root: python scripts/build_gold_043_057.py
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
# NOTE 043 — Allergy / Immunology
# ============================================================
def build_note_043():
    note = (DATA_DIR / "note_043.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_043",
        "specialty": "Allergy / Immunology",
        "source_row_index": 4996,
        "diagnoses": [
            {
                "name_as_written": "asthma",
                "normalised_name": "asthma",
                "status": "active",
                "span": get_span(note, "asthma"),
                "icd_code": "J45.909",
            },
            {
                "name_as_written": "urinary tract infection",
                "normalised_name": "urinary tract infection",
                "status": "historical",
                "span": get_span(note, "urinary tract infection"),
                "icd_code": "N39.0",
            },
            {
                "name_as_written": "allergic rhinitis",
                "normalised_name": "allergic rhinitis",
                "status": "active",
                "span": get_span(note, "allergic rhinitis"),
                "icd_code": "J30.9",
            },
            {
                "name_as_written": "cervical dysplasia",
                "normalised_name": "cervical dysplasia",
                "status": "active",
                "span": get_span(note, "cervical dysplasia"),
                "icd_code": "N87.9",
            },
            {
                "name_as_written": "stress incontinence",
                "normalised_name": "stress incontinence",
                "status": "active",
                "span": get_span(note, "stress incontinence"),
                "icd_code": "N39.3",
            },
            {
                "name_as_written": "Premenstrual dysphoric disorder",
                "normalised_name": "premenstrual dysphoric disorder",
                "status": "active",
                "span": get_span(note, "Premenstrual dysphoric disorder"),
                "icd_code": "F32.81",
            },
            {
                "name_as_written": "Hematuria",
                "normalised_name": "hematuria",
                "status": "active",
                "span": get_span(note, "Hematuria"),
                "icd_code": "R31.9",
            },
        ],
        "medications": [
            {
                "name": "Proventil",
                "dose": None,
                "route": "inhaler",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Proventil"),
            },
            {
                "name": "Allegra",
                "dose": None,
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Allegra"),
            },
            {
                "name": "Flonase",
                "dose": None,
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Flonase"),
            },
            {
                "name": "Advair",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "discontinued",
                "span": get_span(note, "Advair"),
            },
            {
                "name": "Flovent",
                "dose": "44 mcg",
                "route": "p.o.",
                "frequency": "b.i.d.",
                "status": "newly_prescribed",
                "span": get_span(note, "Flovent"),
            },
            {
                "name": "fluoxetine",
                "dose": "20 mg",
                "route": "p.o.",
                "frequency": "q.d.",
                "status": "newly_prescribed",
                "span": get_span(note, "fluoxetine"),
            },
            {
                "name": "calcium",
                "dose": "1200 mg",
                "route": None,
                "frequency": "a day",
                "status": "newly_prescribed",
                "span": get_span(note, "calcium"),
            },
            {
                "name": "vitamin D",
                "dose": "400 U",
                "route": None,
                "frequency": "a day",
                "status": "newly_prescribed",
                "span": get_span(note, "vitamin D"),
            },
        ],
        "procedures": [
            {
                "name": "Pap smear",
                "date": None,
                "span": get_span(note, "Pap smear"),
            },
            {
                "name": "screening mammogram",
                "date": None,
                "span": get_span(note, "screening mammogram"),
            },
            {
                "name": "UA",
                "date": None,
                "span": get_span(note, "UA"),
            },
        ],
        "allergies": [
            {
                "substance": "Sulfa",
                "reaction": None,
                "span": get_span(note, "Sulfa"),
            }
        ],
        "vitals": [
            {
                "name": "Weight",
                "value": "151",
                "unit": "pounds",
                "span": get_span(note, "151 pounds"),
            },
            {
                "name": "Blood pressure",
                "value": "110/60",
                "unit": "mmHg",
                "span": get_span(note, "110/60"),
            },
            {
                "name": "Pulse",
                "value": "72",
                "unit": "bpm",
                "span": get_span(note, "Pulse is 72"),
            },
            {
                "name": "Temperature",
                "value": "97.1",
                "unit": "degrees",
                "span": get_span(note, "97.1 degrees"),
            },
            {
                "name": "Respirations",
                "value": "20",
                "unit": "breaths/min",
                "span": get_span(note, "Respirations are 20"),
            },
        ],
    }


# ============================================================
# NOTE 044 — Autopsy (SPECIAL CASE: major cause of death only)
# ============================================================
def build_note_044():
    note = (DATA_DIR / "note_044.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_044",
        "specialty": "Autopsy",
        "source_row_index": 4986,
        "diagnoses": [
            {
                "name_as_written": "contusion",
                "normalised_name": "contusion",
                "status": "active",
                "span": get_span(note, "contusion"),
                "icd_code": "S40.029A",
            }
        ],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [
            {
                "name": "Length",
                "value": "71",
                "unit": "inches",
                "span": get_span(note, "71 inches"),
            },
            {
                "name": "Weight",
                "value": "178",
                "unit": "pounds",
                "span": get_span(note, "178 pounds"),
            },
        ],
    }


# ============================================================
# NOTE 045 — Bariatrics
# ============================================================
def build_note_045():
    note = (DATA_DIR / "note_045.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_045",
        "specialty": "Bariatrics",
        "source_row_index": 2,
        "diagnoses": [
            {
                "name_as_written": "overweight",
                "normalised_name": "overweight",
                "status": "active",
                "span": get_span(note, "overweight"),
                "icd_code": "E66.3",
            },
            {
                "name_as_written": "high cholesterol",
                "normalised_name": "hypercholesterolemia",
                "status": "active",
                "span": get_span(note, "high cholesterol"),
                "icd_code": "E78.00",
            },
            {
                "name_as_written": "high blood pressure",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "high blood pressure"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "asthma",
                "normalised_name": "asthma",
                "status": "active",
                "span": get_span(note, "asthma"),
                "icd_code": "J45.909",
            },
            {
                "name_as_written": "sleep apnea",
                "normalised_name": "sleep apnea",
                "status": "active",
                "span": get_span(note, "sleep apnea"),
                "icd_code": "G47.30",
            },
            {
                "name_as_written": "diabetic",
                "normalised_name": "diabetes mellitus",
                "status": "active",
                "span": get_span(note, "diabetic"),
                "icd_code": "E11.9",
            },
            {
                "name_as_written": "hemorrhoids",
                "normalised_name": "hemorrhoids",
                "status": "active",
                "span": get_span(note, "hemorrhoids"),
                "icd_code": "K64.9",
            },
            {
                "name_as_written": "gout",
                "normalised_name": "gout",
                "status": "active",
                "span": get_span(note, "gout"),
                "icd_code": "M10.9",
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
                "name_as_written": "pulmonary embolism",
                "normalised_name": "pulmonary embolism",
                "status": "ruled_out",
                "span": get_span(note, "pulmonary embolism"),
                "icd_code": "I26.99",
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
                "name_as_written": "GERD",
                "normalised_name": "gastroesophageal reflux disease",
                "status": "ruled_out",
                "span": get_span(note, "GERD"),
                "icd_code": "K21.9",
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
        "medications": [
            {
                "name": "Diovan",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Diovan"),
            },
            {
                "name": "Crestor",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Crestor"),
            },
            {
                "name": "Tricor",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Tricor"),
            },
            {
                "name": "Chantix",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Chantix"),
            },
        ],
        "procedures": [
            {
                "name": "orthopedic or knee surgery",
                "date": None,
                "span": get_span(note, "orthopedic or knee surgery"),
            },
            {
                "name": "sleep study",
                "date": None,
                "span": get_span(note, "sleep study"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "Weight",
                "value": "344",
                "unit": "pounds",
                "span": get_span(note, "344 pounds"),
            },
            {
                "name": "Height",
                "value": "5'9\"",
                "unit": None,
                "span": get_span(note, "5'9\""),
            },
            {
                "name": "BMI",
                "value": "51",
                "unit": None,
                "span": get_span(note, "BMI of 51"),
            },
        ],
    }


# ============================================================
# NOTE 046 — Cardiovascular / Pulmonary
# ============================================================
def build_note_046():
    note = (DATA_DIR / "note_046.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_046",
        "specialty": "Cardiovascular / Pulmonary",
        "source_row_index": 4949,
        "diagnoses": [
            {
                "name_as_written": "Bronchiolitis",
                "normalised_name": "bronchiolitis",
                "status": "active",
                "span": get_span(note, "Bronchiolitis"),
                "icd_code": "J21.0",
            },
            {
                "name_as_written": "respiratory syncytial virus",
                "normalised_name": "respiratory syncytial virus infection",
                "status": "active",
                "span": get_span(note, "respiratory syncytial virus"),
                "icd_code": "B97.4",
            },
            {
                "name_as_written": "Innocent heart murmur",
                "normalised_name": "innocent heart murmur",
                "status": "active",
                "span": get_span(note, "Innocent heart murmur"),
                "icd_code": "R01.0",
            },
        ],
        "medications": [
            {
                "name": "albuterol",
                "dose": None,
                "route": "inhalation",
                "frequency": "as needed",
                "status": "current",
                "span": get_span(note, "albuterol"),
            }
        ],
        "procedures": [
            {
                "name": "chest x-ray",
                "date": None,
                "span": get_span(note, "chest x-ray"),
            }
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "Weight",
                "value": "3.346",
                "unit": "kg",
                "span": get_span(note, "3.346 kg"),
            }
        ],
    }


# ============================================================
# NOTE 047 — Chiropractic
# ============================================================
def build_note_047():
    note = (DATA_DIR / "note_047.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_047",
        "specialty": "Chiropractic",
        "source_row_index": 4600,
        "diagnoses": [
            {
                "name_as_written": "Left Chopart joint sprain",
                "normalised_name": "chopart joint sprain",
                "status": "active",
                "span": get_span(note, "Left Chopart joint sprain"),
                "icd_code": "S93.492A",
            },
            {
                "name_as_written": "fracture",
                "normalised_name": "fracture",
                "status": "ruled_out",
                "span": get_span(note, "fracture"),
                "icd_code": "S92.909A",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Radiographs",
                "date": None,
                "span": get_span(note, "Radiographs"),
            },
            {
                "name": "MR scan of the ankle",
                "date": "12/01/05",
                "span": get_span(note, "MR scan of the ankle"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 048 — Consult - History and Phy.
# ============================================================
def build_note_048():
    note = (DATA_DIR / "note_048.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_048",
        "specialty": "Consult - History and Phy.",
        "source_row_index": 4421,
        "diagnoses": [
            {
                "name_as_written": "dry eyes",
                "normalised_name": "dry eye syndrome",
                "status": "ruled_out",
                "span": get_span(note, "dry eyes"),
                "icd_code": "H04.123",
            }
        ],
        "medications": [
            {
                "name": "amoxicillin-clavulanate",
                "dose": "125 mg-31.25 mg",
                "route": "tablet, chewable",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "amoxicillin-clavulanate"),
            },
            {
                "name": "Adrenocot",
                "dose": "0.5 mg",
                "route": "tablet",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Adrenocot"),
            },
            {
                "name": "Vioxx",
                "dose": "12.5 mg",
                "route": "tablet",
                "frequency": "BID",
                "status": "current",
                "span": get_span(note, "Vioxx"),
            },
            {
                "name": "Alphagan",
                "dose": "0.2%",
                "route": "ophthalmic",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Alphagan"),
            },
        ],
        "procedures": [
            {
                "name": "appendectomy",
                "date": "1989",
                "span": get_span(note, "appendectomy"),
            },
            {
                "name": "applanation tonometry",
                "date": None,
                "span": get_span(note, "applanation tonometry"),
            },
        ],
        "allergies": [
            {
                "substance": "aspirin",
                "reaction": "disorientation, GI upset",
                "span": get_span(note, "aspirin"),
            }
        ],
        "vitals": [],
    }


# ============================================================
# NOTE 049 — Cosmetic / Plastic Surgery
# ============================================================
def build_note_049():
    note = (DATA_DIR / "note_049.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_049",
        "specialty": "Cosmetic / Plastic Surgery",
        "source_row_index": 4067,
        "diagnoses": [
            {
                "name_as_written": "Bilateral macromastia",
                "normalised_name": "macromastia",
                "status": "active",
                "span": get_span(note, "Bilateral macromastia"),
                "icd_code": "N62",
            }
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Bilateral reduction mammoplasty",
                "date": None,
                "span": get_span(note, "Bilateral reduction mammoplasty"),
            },
            {
                "name": "mammogram",
                "date": None,
                "span": get_span(note, "mammogram"),
            },
            {
                "name": "suction lipectomy",
                "date": None,
                "span": get_span(note, "suction lipectomy"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 050 — Dentistry
# ============================================================
def build_note_050():
    note = (DATA_DIR / "note_050.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_050",
        "specialty": "Dentistry",
        "source_row_index": 4022,
        "diagnoses": [
            {
                "name_as_written": "ODONTALGIA",
                "normalised_name": "odontalgia",
                "status": "active",
                "span": get_span(note, "ODONTALGIA"),
                "icd_code": "K08.89",
            },
            {
                "name_as_written": "MULTIPLE DENTAL CARIES",
                "normalised_name": "dental caries",
                "status": "active",
                "span": get_span(note, "MULTIPLE DENTAL CARIES"),
                "icd_code": "K02.9",
            },
            {
                "name_as_written": "Ludwig's syndrome",
                "normalised_name": "ludwig angina",
                "status": "ruled_out",
                "span": get_span(note, "Ludwig's syndrome"),
                "icd_code": "K12.2",
            },
            {
                "name_as_written": "dental fractures",
                "normalised_name": "tooth fracture",
                "status": "ruled_out",
                "span": get_span(note, "dental fractures"),
                "icd_code": "M27.88",
            },
            {
                "name_as_written": "abscess",
                "normalised_name": "periapical abscess",
                "status": "ruled_out",
                "span": get_span(note, "abscess"),
                "icd_code": "K04.7",
            },
        ],
        "medications": [
            {
                "name": "OxyContin",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "OxyContin"),
            },
            {
                "name": "Vicodin",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Vicodin"),
            },
            {
                "name": "Dilaudid",
                "dose": "4 mg",
                "route": "IM",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Dilaudid"),
            },
            {
                "name": "Percocet",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Percocet"),
            },
            {
                "name": "clindamycin",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "clindamycin"),
            },
        ],
        "procedures": [
            {
                "name": "teeth pulled",
                "date": None,
                "span": get_span(note, "teeth pulled"),
            }
        ],
        "allergies": [
            {
                "substance": "PENICILLIN",
                "reaction": None,
                "span": get_span(note, "PENICILLIN"),
            },
            {
                "substance": "CODEINE",
                "reaction": None,
                "span": get_span(note, "CODEINE"),
            },
        ],
        "vitals": [
            {
                "name": "Temperature",
                "value": "97.9",
                "unit": "°F",
                "span": get_span(note, "97.9"),
            },
            {
                "name": "Blood pressure",
                "value": "146/83",
                "unit": "mmHg",
                "span": get_span(note, "146/83"),
            },
            {
                "name": "Pulse",
                "value": "74",
                "unit": "bpm",
                "span": get_span(note, "pulse is 74"),
            },
            {
                "name": "Respirations",
                "value": "16",
                "unit": "breaths/min",
                "span": get_span(note, "respirations 16"),
            },
            {
                "name": "O2 sat",
                "value": "98%",
                "unit": "%",
                "span": get_span(note, "98%"),
            },
        ],
    }


# ============================================================
# NOTE 051 — Dermatology
# ============================================================
def build_note_051():
    note = (DATA_DIR / "note_051.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_051",
        "specialty": "Dermatology",
        "source_row_index": 4020,
        "diagnoses": [
            {
                "name_as_written": "first and second degree burns",
                "normalised_name": "first and second degree burns",
                "status": "active",
                "span": get_span(note, "first and second degree burns"),
                "icd_code": "T22.20XA",
            }
        ],
        "medications": [
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
                "route": "PO",
                "frequency": "every four hours p.r.n.",
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
# NOTE 052 — Diets and Nutritions
# ============================================================
def build_note_052():
    note = (DATA_DIR / "note_052.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_052",
        "specialty": "Diets and Nutritions",
        "source_row_index": 3993,
        "diagnoses": [
            {
                "name_as_written": "lipids are elevated",
                "normalised_name": "hyperlipidemia",
                "status": "active",
                "span": get_span(note, "lipids are elevated"),
                "icd_code": "E78.5",
            }
        ],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [
            {
                "name": "Height",
                "value": "6 foot 2 inches",
                "unit": None,
                "span": get_span(note, "6 foot 2 inches"),
            },
            {
                "name": "Weight",
                "value": "204",
                "unit": "pounds",
                "span": get_span(note, "204 pounds"),
            },
            {
                "name": "BMI",
                "value": "26.189",
                "unit": None,
                "span": get_span(note, "26.189"),
            },
            {
                "name": "Cholesterol",
                "value": "251",
                "unit": "mg/dL",
                "span": get_span(note, "Cholesterol:  251"),
            },
            {
                "name": "LDL",
                "value": "166",
                "unit": "mg/dL",
                "span": get_span(note, "LDL:  166"),
            },
            {
                "name": "VLDL",
                "value": "17",
                "unit": "mg/dL",
                "span": get_span(note, "VLDL:  17"),
            },
            {
                "name": "HDL",
                "value": "68",
                "unit": "mg/dL",
                "span": get_span(note, "HDL:  68"),
            },
            {
                "name": "Triglycerides",
                "value": "87",
                "unit": "mg/dL",
                "span": get_span(note, "Triglycerides:  87"),
            },
        ],
    }


# ============================================================
# NOTE 053 — Discharge Summary
# ============================================================
def build_note_053():
    note = (DATA_DIR / "note_053.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_053",
        "specialty": "Discharge Summary",
        "source_row_index": 3910,
        "diagnoses": [
            {
                "name_as_written": "Microinvasive carcinoma of the cervix",
                "normalised_name": "cervical carcinoma",
                "status": "active",
                "span": get_span(note, "Microinvasive carcinoma of the cervix"),
                "icd_code": "C53.9",
            },
            {
                "name_as_written": "cystotomy",
                "normalised_name": "intraoperative bladder injury",
                "status": "active",
                "span": get_span(note, "cystotomy"),
                "icd_code": "N99.820",
            },
            {
                "name_as_written": "urinary tract infection",
                "normalised_name": "urinary tract infection",
                "status": "active",
                "span": get_span(note, "urinary tract infection"),
                "icd_code": "N39.0",
            },
        ],
        "medications": [
            {
                "name": "Vicodin",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Vicodin"),
            },
            {
                "name": "Motrin",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Motrin"),
            },
            {
                "name": "Macrodantin",
                "dose": None,
                "route": "PO",
                "frequency": "at bedtime",
                "status": "newly_prescribed",
                "span": get_span(note, "Macrodantin"),
            },
        ],
        "procedures": [
            {
                "name": "Total vaginal hysterectomy",
                "date": "04/02/2007",
                "span": get_span(note, "Total vaginal hysterectomy"),
            },
            {
                "name": "tubal ligation",
                "date": None,
                "span": get_span(note, "tubal ligation"),
            },
            {
                "name": "cone biopsy",
                "date": "02/12/2007",
                "span": get_span(note, "cone biopsy"),
            },
            {
                "name": "Chest x-ray",
                "date": None,
                "span": get_span(note, "Chest x-ray"),
            },
            {
                "name": "Pap smear",
                "date": "80s",
                "span": get_span(note, "Pap smear"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "hemoglobin",
                "value": "10.8",
                "unit": "g/dL",
                "span": get_span(note, "hemoglobin 10.8"),
            }
        ],
    }


# ============================================================
# NOTE 054 — ENT - Otolaryngology
# ============================================================
def build_note_054():
    note = (DATA_DIR / "note_054.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_054",
        "specialty": "ENT - Otolaryngology",
        "source_row_index": 3733,
        "diagnoses": [
            {
                "name_as_written": "Nasal septal deviation",
                "normalised_name": "deviated nasal septum",
                "status": "active",
                "span": get_span(note, "Nasal septal deviation"),
                "icd_code": "J34.2",
            },
            {
                "name_as_written": "bilateral inferior turbinate hypertrophy",
                "normalised_name": "hypertrophy of nasal turbinates",
                "status": "active",
                "span": get_span(note, "bilateral inferior turbinate hypertrophy"),
                "icd_code": "J34.3",
            },
            {
                "name_as_written": "Tonsillitis with hypertrophy",
                "normalised_name": "tonsillitis with hypertrophy",
                "status": "active",
                "span": get_span(note, "Tonsillitis with hypertrophy"),
                "icd_code": "J35.01",
            },
            {
                "name_as_written": "Edema to the uvula and soft palate",
                "normalised_name": "uvular and soft palate edema",
                "status": "active",
                "span": get_span(note, "Edema to the uvula and soft palate"),
                "icd_code": "K12.2",
            },
            {
                "name_as_written": "tonsillolith",
                "normalised_name": "tonsillolith",
                "status": "active",
                "span": get_span(note, "tonsillolith"),
                "icd_code": "J35.8",
            },
            {
                "name_as_written": "halitosis",
                "normalised_name": "halitosis",
                "status": "active",
                "span": get_span(note, "halitosis"),
                "icd_code": "R19.6",
            },
        ],
        "medications": [
            {
                "name": "lidocaine",
                "dose": "1%",
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
                "name": "Afrin",
                "dose": None,
                "route": "topical",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Afrin"),
            },
            {
                "name": "bacitracin",
                "dose": None,
                "route": "topical",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "bacitracin"),
            },
        ],
        "procedures": [
            {
                "name": "Nasal septoplasty",
                "date": None,
                "span": get_span(note, "Nasal septoplasty"),
            },
            {
                "name": "Bilateral submucous resection of the inferior turbinates",
                "date": None,
                "span": get_span(note, "Bilateral submucous resection of the inferior turbinates"),
            },
            {
                "name": "Tonsillectomy and resection of soft palate",
                "date": None,
                "span": get_span(note, "Tonsillectomy and resection of soft palate"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 055 — Emergency Room Reports
# ============================================================
def build_note_055():
    note = (DATA_DIR / "note_055.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_055",
        "specialty": "Emergency Room Reports",
        "source_row_index": 3836,
        "diagnoses": [
            {
                "name_as_written": "pneumonia",
                "normalised_name": "pneumonia",
                "status": "historical",
                "span": get_span(note, "pneumonia"),
                "icd_code": "J18.9",
            },
            {
                "name_as_written": "CHF",
                "normalised_name": "congestive heart failure",
                "status": "active",
                "span": get_span(note, "CHF"),
                "icd_code": "I50.9",
            },
            {
                "name_as_written": "atrial fibrillation",
                "normalised_name": "atrial fibrillation",
                "status": "active",
                "span": get_span(note, "atrial fibrillation"),
                "icd_code": "I48.91",
            },
            {
                "name_as_written": "Renal insufficiency",
                "normalised_name": "renal insufficiency",
                "status": "active",
                "span": get_span(note, "Renal insufficiency"),
                "icd_code": "N18.9",
            },
            {
                "name_as_written": "Coronary artery disease",
                "normalised_name": "coronary artery disease",
                "status": "active",
                "span": get_span(note, "Coronary artery disease"),
                "icd_code": "I25.10",
            },
            {
                "name_as_written": "COPD",
                "normalised_name": "chronic obstructive pulmonary disease",
                "status": "active",
                "span": get_span(note, "COPD"),
                "icd_code": "J44.9",
            },
            {
                "name_as_written": "Bladder cancer",
                "normalised_name": "bladder cancer",
                "status": "active",
                "span": get_span(note, "Bladder cancer"),
                "icd_code": "C67.9",
            },
            {
                "name_as_written": "ruptured colon",
                "normalised_name": "colon rupture",
                "status": "historical",
                "span": get_span(note, "ruptured colon"),
                "icd_code": "K63.1",
            },
            {
                "name_as_written": "Myocardial infarction",
                "normalised_name": "myocardial infarction",
                "status": "historical",
                "span": get_span(note, "Myocardial infarction"),
                "icd_code": "I21.9",
            },
            {
                "name_as_written": "Coagulopathy",
                "normalised_name": "anticoagulant-induced coagulopathy",
                "status": "active",
                "span": get_span(note, "Coagulopathy"),
                "icd_code": "D68.32",
            },
        ],
        "medications": [
            {
                "name": "Coumadin",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "discontinued",
                "span": get_span(note, "Coumadin"),
            },
            {
                "name": "Simvastatin",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Simvastatin"),
            },
            {
                "name": "Nitrofurantoin",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Nitrofurantoin"),
            },
            {
                "name": "Celebrex",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Celebrex"),
            },
            {
                "name": "Digoxin",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Digoxin"),
            },
            {
                "name": "Levothyroxine",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Levothyroxine"),
            },
            {
                "name": "Vicodin",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Vicodin"),
            },
            {
                "name": "Triamterene",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Triamterene"),
            },
            {
                "name": "hydrochlorothiazide",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "hydrochlorothiazide"),
            },
            {
                "name": "Carvedilol",
                "dose": None,
                "route": "PO",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Carvedilol"),
            },
            {
                "name": "vitamin K",
                "dose": "10 mg in 100 mL of D5W",
                "route": "IV",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "vitamin K"),
            },
            {
                "name": "aspirin",
                "dose": "one",
                "route": "PO",
                "frequency": "a day",
                "status": "newly_prescribed",
                "span": get_span(note, "aspirin"),
            },
        ],
        "procedures": [
            {
                "name": "Hernia repair",
                "date": None,
                "span": get_span(note, "Hernia repair"),
            },
            {
                "name": "Colon resection",
                "date": None,
                "span": get_span(note, "Colon resection"),
            },
            {
                "name": "Carpal tunnel repair",
                "date": None,
                "span": get_span(note, "Carpal tunnel repair"),
            },
            {
                "name": "Knee surgery",
                "date": None,
                "span": get_span(note, "Knee surgery"),
            },
            {
                "name": "PT/INR",
                "date": None,
                "span": get_span(note, "PT/INR"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "Blood pressure",
                "value": "100/46",
                "unit": "mmHg",
                "span": get_span(note, "100/46"),
            },
            {
                "name": "Pulse",
                "value": "75",
                "unit": "bpm",
                "span": get_span(note, "pulse of 75"),
            },
            {
                "name": "Respirations",
                "value": "12",
                "unit": "breaths/min",
                "span": get_span(note, "respirations 12"),
            },
            {
                "name": "Temperature",
                "value": "98.2",
                "unit": "°F",
                "span": get_span(note, "98.2"),
            },
        ],
    }


# ============================================================
# NOTE 056 — Endocrinology
# ============================================================
def build_note_056():
    note = (DATA_DIR / "note_056.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_056",
        "specialty": "Endocrinology",
        "source_row_index": 3793,
        "diagnoses": [
            {
                "name_as_written": "pneumonitis",
                "normalised_name": "pneumonitis",
                "status": "active",
                "span": get_span(note, "pneumonitis"),
                "icd_code": "J18.9",
            },
            {
                "name_as_written": "left adrenal nodule",
                "normalised_name": "adrenal adenoma",
                "status": "suspected",
                "span": get_span(note, "left adrenal nodule"),
                "icd_code": "D35.02",
            },
            {
                "name_as_written": "pancreatic lesion",
                "normalised_name": "pancreatic cystic lesion",
                "status": "active",
                "span": get_span(note, "pancreatic lesion"),
                "icd_code": "K86.89",
            },
            {
                "name_as_written": "adenomatous polyps",
                "normalised_name": "adenomatous colon polyps",
                "status": "historical",
                "span": get_span(note, "adenomatous polyps"),
                "icd_code": "D12.6",
            },
            {
                "name_as_written": "hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "type 2 diabetes mellitus",
                "normalised_name": "type 2 diabetes mellitus",
                "status": "active",
                "span": get_span(note, "type 2 diabetes mellitus"),
                "icd_code": "E11.9",
            },
            {
                "name_as_written": "asthma",
                "normalised_name": "asthma",
                "status": "active",
                "span": get_span(note, "asthma"),
                "icd_code": "J45.909",
            },
            {
                "name_as_written": "high cholesterol",
                "normalised_name": "hypercholesterolemia",
                "status": "active",
                "span": get_span(note, "high cholesterol"),
                "icd_code": "E78.00",
            },
            {
                "name_as_written": "obese",
                "normalised_name": "obesity",
                "status": "active",
                "span": get_span(note, "obese"),
                "icd_code": "E66.9",
            },
            {
                "name_as_written": "bleeding disorders",
                "normalised_name": "coagulation defect",
                "status": "ruled_out",
                "span": get_span(note, "bleeding disorders"),
                "icd_code": "D68.9",
            },
        ],
        "medications": [
            {
                "name": "glipizide",
                "dose": "5 mg",
                "route": "PO",
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "glipizide"),
            },
            {
                "name": "metformin",
                "dose": "500 mg",
                "route": "PO",
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "metformin"),
            },
            {
                "name": "Atacand",
                "dose": "16 mg",
                "route": "PO",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Atacand"),
            },
            {
                "name": "metoprolol",
                "dose": "25 mg",
                "route": "PO",
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "metoprolol"),
            },
            {
                "name": "Lipitor",
                "dose": "10 mg",
                "route": "PO",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Lipitor"),
            },
            {
                "name": "pantoprazole",
                "dose": "40 mg",
                "route": "PO",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "pantoprazole"),
            },
            {
                "name": "Flomax",
                "dose": "0.4 mg",
                "route": "PO",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Flomax"),
            },
            {
                "name": "Detrol",
                "dose": "4 mg",
                "route": "PO",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Detrol"),
            },
            {
                "name": "Zyrtec",
                "dose": "10 mg",
                "route": "PO",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Zyrtec"),
            },
            {
                "name": "Advair Diskus",
                "dose": "100/50 mcg",
                "route": "inhalation",
                "frequency": "one puff b.i.d.",
                "status": "current",
                "span": get_span(note, "Advair Diskus"),
            },
            {
                "name": "fluticasone spray",
                "dose": "50 mcg",
                "route": "nasal",
                "frequency": "two sprays daily",
                "status": "current",
                "span": get_span(note, "fluticasone spray"),
            },
        ],
        "procedures": [
            {
                "name": "CAT scan",
                "date": None,
                "span": get_span(note, "CAT scan"),
            },
            {
                "name": "MRI",
                "date": None,
                "span": get_span(note, "MRI"),
            },
            {
                "name": "colonoscopy",
                "date": "September of last year",
                "span": get_span(note, "colonoscopy"),
            },
            {
                "name": "esophagogastroduodenoscopy",
                "date": None,
                "span": get_span(note, "esophagogastroduodenoscopy"),
            },
        ],
        "allergies": [
            {
                "substance": "ENVIRONMENTAL",
                "reaction": None,
                "span": get_span(note, "ENVIRONMENTAL"),
            }
        ],
        "vitals": [],
    }


# ============================================================
# NOTE 057 — Gastroenterology
# ============================================================
def build_note_057():
    note = (DATA_DIR / "note_057.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_057",
        "specialty": "Gastroenterology",
        "source_row_index": 3578,
        "diagnoses": [
            {
                "name_as_written": "Anemia",
                "normalised_name": "anemia",
                "status": "active",
                "span": get_span(note, "Anemia"),
                "icd_code": "D64.9",
            },
            {
                "name_as_written": "Severe duodenitis",
                "normalised_name": "duodenitis",
                "status": "active",
                "span": get_span(note, "Severe duodenitis"),
                "icd_code": "K29.80",
            },
            {
                "name_as_written": "ulceration",
                "normalised_name": "gastroesophageal junction ulcer",
                "status": "active",
                "span": get_span(note, "ulceration"),
                "icd_code": "K22.10",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Upper gastrointestinal endoscopy",
                "date": None,
                "span": get_span(note, "Upper gastrointestinal endoscopy"),
            }
        ],
        "allergies": [],
        "vitals": [],
    }


def main():
    builders = [
        ("note_043", build_note_043),
        ("note_044", build_note_044),
        ("note_045", build_note_045),
        ("note_046", build_note_046),
        ("note_047", build_note_047),
        ("note_048", build_note_048),
        ("note_049", build_note_049),
        ("note_050", build_note_050),
        ("note_051", build_note_051),
        ("note_052", build_note_052),
        ("note_053", build_note_053),
        ("note_054", build_note_054),
        ("note_055", build_note_055),
        ("note_056", build_note_056),
        ("note_057", build_note_057),
    ]

    all_passed = True
    for note_id, builder in builders:
        data = builder()
        ok = write_and_verify(note_id, data)
        if not ok:
            all_passed = False

    if all_passed:
        print("\nAll 15 notes built and verified successfully!")
    else:
        print("\nSome notes had errors!")


if __name__ == "__main__":
    main()
