"""
Build gold/note_058.json through gold/note_072.json.
Run from project root: python scripts/build_gold_058_072.py
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
# NOTE 058 — Allergy / Immunology
# ============================================================
def build_note_058():
    note = (DATA_DIR / "note_058.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_058",
        "specialty": "Allergy / Immunology",
        "source_row_index": 4994,
        "diagnoses": [
            {
                "name_as_written": "chronic sinusitis",
                "normalised_name": "chronic sinusitis",
                "status": "active",
                "span": get_span(note, "chronic sinusitis"),
                "icd_code": "J32.9",
            },
            {
                "name_as_written": "sensorineural hearing loss",
                "normalised_name": "sensorineural hearing loss",
                "status": "active",
                "span": get_span(note, "sensorineural hearing loss"),
                "icd_code": "H90.5",
            },
            {
                "name_as_written": "Seasonal allergies",
                "normalised_name": "seasonal allergies",
                "status": "active",
                "span": get_span(note, "Seasonal allergies"),
                "icd_code": "J30.2",
            },
            {
                "name_as_written": "food allergies",
                "normalised_name": "food allergy",
                "status": "suspected",
                "span": get_span(note, "food allergies"),
                "icd_code": "Z91.018",
            },
            {
                "name_as_written": "hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "orthostatic hypotension",
                "normalised_name": "orthostatic hypotension",
                "status": "ruled_out",
                "span": get_span(note, "orthostatic hypotension"),
                "icd_code": "I95.1",
            },
            {
                "name_as_written": "acute sinusitis",
                "normalised_name": "acute sinusitis",
                "status": "ruled_out",
                "span": get_span(note, "acute sinusitis"),
                "icd_code": "J01.90",
            },
            {
                "name_as_written": "allergic rhinitis",
                "normalised_name": "allergic rhinitis",
                "status": "active",
                "span": get_span(note, "allergic rhinitis"),
                "icd_code": "J30.9",
            },
            {
                "name_as_written": "positional vertigo",
                "normalised_name": "benign paroxysmal positional vertigo",
                "status": "suspected",
                "span": get_span(note, "positional vertigo"),
                "icd_code": "H81.10",
            },
            {
                "name_as_written": "vestibular neuronitis",
                "normalised_name": "vestibular neuronitis",
                "status": "suspected",
                "span": get_span(note, "vestibular neuronitis"),
                "icd_code": "H81.20",
            },
            {
                "name_as_written": "Inferior turbinate hypertrophy",
                "normalised_name": "inferior turbinate hypertrophy",
                "status": "active",
                "span": get_span(note, "Inferior turbinate hypertrophy"),
                "icd_code": "J34.3",
            },
            {
                "name_as_written": "Nasal septum deformity",
                "normalised_name": "nasal septum deformity",
                "status": "active",
                "span": get_span(note, "Nasal septum deformity"),
                "icd_code": "J34.2",
            },
        ],
        "medications": [
            {
                "name": "Allegra",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "discontinued",
                "span": get_span(note, "Allegra"),
            },
            {
                "name": "DynaCirc",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "DynaCirc"),
            },
            {
                "name": "Veramyst",
                "dose": "two sprays each nostril",
                "route": "nasal",
                "frequency": "daily and even twice daily if symptoms are worsening",
                "status": "newly_prescribed",
                "span": get_span(note, "Veramyst nasal spray"),
            },
            {
                "name": "Medrol",
                "dose": None,
                "route": None,
                "frequency": "as directed",
                "status": "newly_prescribed",
                "span": get_span(note, "Medrol Dosepak"),
            },
            {
                "name": "Clarinex",
                "dose": "5 mg",
                "route": None,
                "frequency": "daily",
                "status": "newly_prescribed",
                "span": get_span(note, "Clarinex"),
            },
        ],
        "procedures": [
            {
                "name": "CT of her paranasal sinuses",
                "date": None,
                "span": get_span(note, "CT of her paranasal sinuses"),
            },
            {
                "name": "audiogram",
                "date": None,
                "span": get_span(note, "audiogram"),
            },
            {
                "name": "Lower extremity vein stripping",
                "date": None,
                "span": get_span(note, "Lower extremity vein stripping"),
            },
            {
                "name": "tonsillectomy and adenoidectomy",
                "date": None,
                "span": get_span(note, "tonsillectomy and adenoidectomy"),
            },
            {
                "name": "Fiberoptic nasopharyngoscopy",
                "date": None,
                "span": get_span(note, "Fiberoptic nasopharyngoscopy"),
            },
        ],
        "allergies": [
            {
                "substance": "Egg-based products",
                "reaction": "hives",
                "span": get_span(note, "Egg-based products cause hives"),
            }
        ],
        "vitals": [
            {
                "name": "Blood pressure",
                "value": "136/74",
                "unit": "mmHg",
                "span": get_span(note, "136/74"),
            },
            {
                "name": "pulse",
                "value": "84",
                "unit": "bpm",
                "span": get_span(note, "pulse 84"),
            },
            {
                "name": "temperature",
                "value": "98.4",
                "unit": "°F",
                "span": get_span(note, "temperature is 98.4"),
            },
            {
                "name": "weight",
                "value": "180",
                "unit": "pounds",
                "span": get_span(note, "weight is 180 pounds"),
            },
            {
                "name": "height",
                "value": "5 feet 3 inches",
                "unit": None,
                "span": get_span(note, "5 feet 3 inches"),
            },
        ],
    }


# ============================================================
# NOTE 059 — Autopsy (SPECIAL CASE: major cause of death only)
# ============================================================
def build_note_059():
    note = (DATA_DIR / "note_059.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_059",
        "specialty": "Autopsy",
        "source_row_index": 4987,
        "diagnoses": [
            {
                "name_as_written": "Sharp force wound of neck",
                "normalised_name": "sharp force injury of neck",
                "status": "active",
                "span": get_span(note, "Sharp force wound of neck"),
                "icd_code": "S11.90XA",
            },
            {
                "name_as_written": "transection of left internal jugular vein",
                "normalised_name": "laceration of internal jugular vein",
                "status": "active",
                "span": get_span(note, "transection of left internal jugular vein"),
                "icd_code": "S15.112A",
            },
            {
                "name_as_written": "hemothorax",
                "normalised_name": "traumatic hemothorax",
                "status": "active",
                "span": get_span(note, "hemothorax"),
                "icd_code": "S27.1XXA",
            },
            {
                "name_as_written": "hemoperitoneum",
                "normalised_name": "traumatic hemoperitoneum",
                "status": "active",
                "span": get_span(note, "hemoperitoneum"),
                "icd_code": "S36.899A",
            },
        ],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [
            {
                "name": "Weight",
                "value": "171",
                "unit": "pounds",
                "span": get_span(note, "171 pounds"),
            },
            {
                "name": "Length",
                "value": "69",
                "unit": "inches",
                "span": get_span(note, "69 inches"),
            },
        ],
    }


# ============================================================
# NOTE 060 — Bariatrics
# ============================================================
def build_note_060():
    note = (DATA_DIR / "note_060.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_060",
        "specialty": "Bariatrics",
        "source_row_index": 5,
        "diagnoses": [
            {
                "name_as_written": "Morbid obesity",
                "normalised_name": "morbid obesity",
                "status": "active",
                "span": get_span(note, "Morbid obesity"),
                "icd_code": "E66.01",
            },
            {
                "name_as_written": "overweight",
                "normalised_name": "overweight",
                "status": "active",
                "span": get_span(note, "overweight"),
                "icd_code": "E66.3",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Laparoscopic antecolic antegastric Roux-en-Y gastric bypass with EEA anastomosis",
                "date": None,
                "span": get_span(note, "Laparoscopic antecolic antegastric Roux-en-Y gastric bypass with EEA anastomosis"),
            },
            {
                "name": "endotracheal intubation",
                "date": None,
                "span": get_span(note, "endotracheal intubation"),
            },
            {
                "name": "Foley catheter",
                "date": None,
                "span": get_span(note, "Foley catheter"),
            },
            {
                "name": "EGD scope",
                "date": None,
                "span": get_span(note, "EGD scope"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 061 — Cardiovascular / Pulmonary
# ============================================================
def build_note_061():
    note = (DATA_DIR / "note_061.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_061",
        "specialty": "Cardiovascular / Pulmonary",
        "source_row_index": 4878,
        "diagnoses": [
            {
                "name_as_written": "syncopal spells",
                "normalised_name": "syncope",
                "status": "suspected",
                "span": get_span(note, "syncopal spells"),
                "icd_code": "R55",
            },
            {
                "name_as_written": "orthostatic changes",
                "normalised_name": "orthostatic hypotension",
                "status": "ruled_out",
                "span": get_span(note, "orthostatic changes"),
                "icd_code": "I95.1",
            },
            {
                "name_as_written": "overweight",
                "normalised_name": "overweight",
                "status": "active",
                "span": get_span(note, "overweight"),
                "icd_code": "E66.3",
            },
        ],
        "medications": [
            {
                "name": "Naprosyn",
                "dose": None,
                "route": None,
                "frequency": "up to six a day",
                "status": "current",
                "span": get_span(note, "Naprosyn"),
            },
            {
                "name": "Flexeril",
                "dose": "10 mg",
                "route": None,
                "frequency": "q 6 p.r.n.",
                "status": "newly_prescribed",
                "span": get_span(note, "Flexeril"),
            },
        ],
        "procedures": [
            {
                "name": "partial hysterectomy",
                "date": "January of 2009",
                "span": get_span(note, "partial hysterectomy"),
            },
            {
                "name": "EKG",
                "date": None,
                "span": get_span(note, "EKG"),
            },
            {
                "name": "ECHOCARDIOGRAM",
                "date": None,
                "span": get_span(note, "ECHOCARDIOGRAM"),
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
                "name": "BP",
                "value": "130/70",
                "unit": "mmHg",
                "span": get_span(note, "130/70"),
            },
            {
                "name": "PR",
                "value": "72",
                "unit": "bpm",
                "span": get_span(note, "PR:  72"),
            },
            {
                "name": "WT",
                "value": "206",
                "unit": "pounds",
                "span": get_span(note, "206 pounds"),
            },
        ],
    }


# ============================================================
# NOTE 062 — Chiropractic
# ============================================================
def build_note_062():
    note = (DATA_DIR / "note_062.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_062",
        "specialty": "Chiropractic",
        "source_row_index": 4604,
        "diagnoses": [
            {
                "name_as_written": "disc desiccation",
                "normalised_name": "intervertebral disc degeneration",
                "status": "active",
                "span": get_span(note, "disc desiccation"),
                "icd_code": "M50.30",
            },
            {
                "name_as_written": "disc herniation",
                "normalised_name": "cervical disc herniation",
                "status": "active",
                "span": get_span(note, "disc herniation"),
                "icd_code": "M50.20",
            },
            {
                "name_as_written": "uncovertebral joint arthrosis",
                "normalised_name": "uncovertebral arthrosis",
                "status": "active",
                "span": get_span(note, "uncovertebral joint arthrosis"),
                "icd_code": "M47.812",
            },
            {
                "name_as_written": "disc osteophyte complex",
                "normalised_name": "cervical disc osteophyte complex",
                "status": "active",
                "span": get_span(note, "disc osteophyte complex"),
                "icd_code": "M47.812",
            },
            {
                "name_as_written": "apophyseal joint arthrosis",
                "normalised_name": "facet joint arthrosis",
                "status": "active",
                "span": get_span(note, "apophyseal joint arthrosis"),
                "icd_code": "M47.812",
            },
            {
                "name_as_written": "central canal stenosis",
                "normalised_name": "cervical spinal stenosis",
                "status": "active",
                "span": get_span(note, "central canal stenosis"),
                "icd_code": "M48.02",
            },
            {
                "name_as_written": "Multilevel degenerative disc disease",
                "normalised_name": "multilevel degenerative disc disease",
                "status": "active",
                "span": get_span(note, "Multilevel degenerative disc disease"),
                "icd_code": "M50.30",
            },
        ],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 063 — Consult - History and Phy.
# ============================================================
def build_note_063():
    note = (DATA_DIR / "note_063.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_063",
        "specialty": "Consult - History and Phy.",
        "source_row_index": 4128,
        "diagnoses": [
            {
                "name_as_written": "Sepsis",
                "normalised_name": "sepsis",
                "status": "active",
                "span": get_span(note, "Sepsis"),
                "icd_code": "A41.9",
            },
            {
                "name_as_written": "outlet obstruction",
                "normalised_name": "bladder outlet obstruction",
                "status": "suspected",
                "span": get_span(note, "outlet obstruction"),
                "icd_code": "N32.0",
            },
            {
                "name_as_written": "hydronephrosis",
                "normalised_name": "hydronephrosis",
                "status": "active",
                "span": get_span(note, "hydronephrosis"),
                "icd_code": "N13.30",
            },
            {
                "name_as_written": "hydroureter",
                "normalised_name": "hydroureter",
                "status": "active",
                "span": get_span(note, "hydroureter"),
                "icd_code": "N13.4",
            },
            {
                "name_as_written": "CAD",
                "normalised_name": "coronary artery disease",
                "status": "historical",
                "span": get_span(note, "CAD"),
                "icd_code": "I25.10",
            },
            {
                "name_as_written": "dementia",
                "normalised_name": "dementia",
                "status": "historical",
                "span": get_span(note, "dementia"),
                "icd_code": "F03.90",
            },
            {
                "name_as_written": "CVA",
                "normalised_name": "cerebrovascular accident",
                "status": "historical",
                "span": get_span(note, "CVA"),
                "icd_code": "I63.9",
            },
            {
                "name_as_written": "nephrolithiasis",
                "normalised_name": "nephrolithiasis",
                "status": "historical",
                "span": get_span(note, "nephrolithiasis"),
                "icd_code": "N20.0",
            },
        ],
        "medications": [
            {
                "name": "Ambien",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Ambien"),
            },
            {
                "name": "Milk of magnesia",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Milk of magnesia"),
            },
            {
                "name": "Tylenol",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Tylenol"),
            },
            {
                "name": "Tramadol",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Tramadol"),
            },
            {
                "name": "Soma",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Soma"),
            },
            {
                "name": "Coumadin",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Coumadin"),
            },
            {
                "name": "Zoloft",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Zoloft"),
            },
            {
                "name": "Allopurinol",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Allopurinol"),
            },
            {
                "name": "Digoxin",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Digoxin"),
            },
            {
                "name": "Namenda",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Namenda"),
            },
            {
                "name": "Zocor",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Zocor"),
            },
            {
                "name": "BuSpar",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "BuSpar"),
            },
            {
                "name": "Detrol",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Detrol"),
            },
            {
                "name": "Coreg",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Coreg"),
            },
            {
                "name": "Colace",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Colace"),
            },
            {
                "name": "Calcium",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Calcium"),
            },
            {
                "name": "Zantac",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Zantac"),
            },
            {
                "name": "Lasix",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Lasix"),
            },
            {
                "name": "Seroquel",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Seroquel"),
            },
            {
                "name": "Aldactone",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Aldactone"),
            },
            {
                "name": "Amoxicillin",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Amoxicillin"),
            },
            {
                "name": "antibiotics",
                "dose": None,
                "route": "IV",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "IV antibiotics"),
            },
        ],
        "procedures": [
            {
                "name": "CT scan",
                "date": None,
                "span": get_span(note, "CT scan"),
            }
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "Pulse",
                "value": "52",
                "unit": "bpm",
                "span": get_span(note, "Pulse 52"),
            },
            {
                "name": "respirations",
                "value": "20",
                "unit": "breaths/min",
                "span": get_span(note, "respirations 20"),
            },
            {
                "name": "blood pressure",
                "value": "104/41",
                "unit": "mmHg",
                "span": get_span(note, "104/41"),
            },
            {
                "name": "O2 sat",
                "value": "98%",
                "unit": "%",
                "span": get_span(note, "saturating 98%"),
            },
        ],
    }


# ============================================================
# NOTE 064 — Cosmetic / Plastic Surgery
# ============================================================
def build_note_064():
    note = (DATA_DIR / "note_064.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_064",
        "specialty": "Cosmetic / Plastic Surgery",
        "source_row_index": 4065,
        "diagnoses": [
            {
                "name_as_written": "Hemangioma, nasal tip",
                "normalised_name": "hemangioma of nasal tip",
                "status": "active",
                "span": get_span(note, "Hemangioma, nasal tip"),
                "icd_code": "D18.00",
            }
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Debulking of hemangioma of the nasal tip through an open rhinoplasty approach",
                "date": None,
                "span": get_span(note, "Debulking of hemangioma of the nasal tip through an open rhinoplasty approach"),
            },
            {
                "name": "Rhinoplasty",
                "date": None,
                "span": get_span(note, "Rhinoplasty"),
            },
            {
                "name": "oroendotracheal tube",
                "date": None,
                "span": get_span(note, "oroendotracheal tube"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 065 — Dentistry
# ============================================================
def build_note_065():
    note = (DATA_DIR / "note_065.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_065",
        "specialty": "Dentistry",
        "source_row_index": 4039,
        "diagnoses": [
            {
                "name_as_written": "Right buccal and canine's base infection",
                "normalised_name": "facial space infection",
                "status": "active",
                "span": get_span(note, "Right buccal and canine's base infection"),
                "icd_code": "K12.2",
            },
            {
                "name_as_written": "necrotic teeth",
                "normalised_name": "pulp necrosis",
                "status": "active",
                "span": get_span(note, "necrotic teeth"),
                "icd_code": "K04.1",
            },
            {
                "name_as_written": "facial abscess",
                "normalised_name": "facial abscess",
                "status": "active",
                "span": get_span(note, "facial abscess"),
                "icd_code": "K12.2",
            },
            {
                "name_as_written": "decay",
                "normalised_name": "dental caries",
                "status": "active",
                "span": get_span(note, "decay"),
                "icd_code": "K02.9",
            },
        ],
        "medications": [
            {
                "name": "antibiotics",
                "dose": None,
                "route": "IV",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "IV antibiotics"),
            }
        ],
        "procedures": [
            {
                "name": "Incision and drainage of multiple facial spaces",
                "date": None,
                "span": get_span(note, "Incision and drainage of multiple facial spaces"),
            },
            {
                "name": "Surgical removal of the following teeth",
                "date": None,
                "span": get_span(note, "Surgical removal of the following teeth"),
            },
            {
                "name": "Penrose drain",
                "date": None,
                "span": get_span(note, "Penrose drain"),
            },
            {
                "name": "nasal endotracheal intubation",
                "date": None,
                "span": get_span(note, "nasal endotracheal intubation"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 066 — Dermatology
# ============================================================
def build_note_066():
    note = (DATA_DIR / "note_066.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_066",
        "specialty": "Dermatology",
        "source_row_index": 3998,
        "diagnoses": [
            {
                "name_as_written": "scalp mole",
                "normalised_name": "melanocytic nevus of scalp",
                "status": "active",
                "span": get_span(note, "scalp mole"),
                "icd_code": "D22.4",
            },
            {
                "name_as_written": "pneumonia",
                "normalised_name": "pneumonia",
                "status": "active",
                "span": get_span(note, "pneumonia"),
                "icd_code": "J18.9",
            },
            {
                "name_as_written": "effusion",
                "normalised_name": "pleural effusion",
                "status": "active",
                "span": get_span(note, "effusion"),
                "icd_code": "J90",
            },
            {
                "name_as_written": "metastatic melanoma",
                "normalised_name": "metastatic malignant melanoma",
                "status": "suspected",
                "span": get_span(note, "metastatic melanoma"),
                "icd_code": "C79.89",
            },
        ],
        "medications": [
            {
                "name": "antibiotic ointment",
                "dose": None,
                "route": "topical",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "antibiotic ointment"),
            }
        ],
        "procedures": [
            {
                "name": "Skin biopsy",
                "date": None,
                "span": get_span(note, "Skin biopsy"),
            },
            {
                "name": "punch biopsy",
                "date": None,
                "span": get_span(note, "punch biopsy"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 067 — Diets and Nutritions
# ============================================================
def build_note_067():
    note = (DATA_DIR / "note_067.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_067",
        "specialty": "Diets and Nutritions",
        "source_row_index": 3989,
        "diagnoses": [
            {
                "name_as_written": "gestational diabetes",
                "normalised_name": "gestational diabetes mellitus",
                "status": "active",
                "span": get_span(note, "gestational diabetes"),
                "icd_code": "O24.419",
            },
            {
                "name_as_written": "obesity",
                "normalised_name": "obesity",
                "status": "active",
                "span": get_span(note, "obesity"),
                "icd_code": "E66.9",
            },
        ],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [
            {
                "name": "weight",
                "value": "155.5",
                "unit": "pounds",
                "span": get_span(note, "155.5 pounds"),
            }
        ],
    }


# ============================================================
# NOTE 068 — Discharge Summary
# ============================================================
def build_note_068():
    note = (DATA_DIR / "note_068.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_068",
        "specialty": "Discharge Summary",
        "source_row_index": 3909,
        "diagnoses": [
            {
                "name_as_written": "Kawasaki disease",
                "normalised_name": "kawasaki disease",
                "status": "active",
                "span": get_span(note, "Kawasaki disease"),
                "icd_code": "M30.3",
            },
            {
                "name_as_written": "conjunctivitis",
                "normalised_name": "conjunctivitis",
                "status": "historical",
                "span": get_span(note, "conjunctivitis"),
                "icd_code": "H10.9",
            },
            {
                "name_as_written": "arthritis",
                "normalised_name": "arthritis",
                "status": "active",
                "span": get_span(note, "arthritis"),
                "icd_code": "M13.9",
            },
            {
                "name_as_written": "thrombocytosis",
                "normalised_name": "thrombocytosis",
                "status": "active",
                "span": get_span(note, "thrombocytosis"),
                "icd_code": "D75.839",
            },
        ],
        "medications": [
            {
                "name": "aspirin",
                "dose": "340 mg",
                "route": None,
                "frequency": "q.6h. for 1 day",
                "status": "newly_prescribed",
                "span": get_span(note, "aspirin"),
            },
            {
                "name": "Prevacid",
                "dose": "15 mg",
                "route": "p.o.",
                "frequency": "once a day",
                "status": "newly_prescribed",
                "span": get_span(note, "Prevacid"),
            },
            {
                "name": "IVIG",
                "dose": None,
                "route": "IV",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "IVIG"),
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
                "name": "fever",
                "value": "102",
                "unit": "°F",
                "span": get_span(note, "fever of 102"),
            }
        ],
    }


# ============================================================
# NOTE 069 — ENT - Otolaryngology
# ============================================================
def build_note_069():
    note = (DATA_DIR / "note_069.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_069",
        "specialty": "ENT - Otolaryngology",
        "source_row_index": 3737,
        "diagnoses": [
            {
                "name_as_written": "Chronic eustachian tube dysfunction",
                "normalised_name": "chronic eustachian tube dysfunction",
                "status": "active",
                "span": get_span(note, "Chronic eustachian tube dysfunction"),
                "icd_code": "H69.80",
            },
            {
                "name_as_written": "Retained right pressure equalization tube",
                "normalised_name": "retained tympanostomy tube",
                "status": "active",
                "span": get_span(note, "Retained right pressure equalization tube"),
                "icd_code": "H74.8X1",
            },
            {
                "name_as_written": "Retracted left tympanic membrane",
                "normalised_name": "retraction of tympanic membrane",
                "status": "active",
                "span": get_span(note, "Retracted left tympanic membrane"),
                "icd_code": "H73.812",
            },
            {
                "name_as_written": "conductive loss",
                "normalised_name": "conductive hearing loss",
                "status": "active",
                "span": get_span(note, "conductive loss"),
                "icd_code": "H90.2",
            },
            {
                "name_as_written": "myringosclerosis",
                "normalised_name": "myringosclerosis",
                "status": "active",
                "span": get_span(note, "myringosclerosis"),
                "icd_code": "H74.01",
            },
            {
                "name_as_written": "perforation in tympanic membrane",
                "normalised_name": "tympanic membrane perforation",
                "status": "active",
                "span": get_span(note, "perforation in tympanic membrane"),
                "icd_code": "H72.90",
            },
        ],
        "medications": [
            {
                "name": "ciprofloxacin",
                "dose": "Three drops",
                "route": "otic",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "ciprofloxacin"),
            }
        ],
        "procedures": [
            {
                "name": "Removal of the old right pressure equalizing tube",
                "date": None,
                "span": get_span(note, "Removal of the old right pressure equalizing tube"),
            },
            {
                "name": "Myringotomy with placement of a left pressure equalizing tube",
                "date": None,
                "span": get_span(note, "Myringotomy with placement of a left pressure equalizing tube"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 070 — Emergency Room Reports
# ============================================================
def build_note_070():
    note = (DATA_DIR / "note_070.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_070",
        "specialty": "Emergency Room Reports",
        "source_row_index": 3837,
        "diagnoses": [
            {
                "name_as_written": "hyperbilirubinemia",
                "normalised_name": "neonatal hyperbilirubinemia",
                "status": "active",
                "span": get_span(note, "hyperbilirubinemia"),
                "icd_code": "P59.9",
            },
            {
                "name_as_written": "hypoxia",
                "normalised_name": "hypoxia",
                "status": "active",
                "span": get_span(note, "hypoxia"),
                "icd_code": "R09.02",
            },
            {
                "name_as_written": "septic",
                "normalised_name": "neonatal sepsis",
                "status": "suspected",
                "span": get_span(note, "septic"),
                "icd_code": "P36.9",
            },
            {
                "name_as_written": "murmur",
                "normalised_name": "heart murmur",
                "status": "active",
                "span": get_span(note, "murmur"),
                "icd_code": "R01.1",
            },
            {
                "name_as_written": "umbilical hernia",
                "normalised_name": "umbilical hernia",
                "status": "active",
                "span": get_span(note, "umbilical hernia"),
                "icd_code": "K42.9",
            },
            {
                "name_as_written": "cephalhematoma",
                "normalised_name": "cephalhematoma",
                "status": "active",
                "span": get_span(note, "cephalhematoma"),
                "icd_code": "P12.0",
            },
            {
                "name_as_written": "ABO incompatibility",
                "normalised_name": "ABO incompatibility",
                "status": "suspected",
                "span": get_span(note, "ABO incompatibility"),
                "icd_code": "P55.1",
            },
            {
                "name_as_written": "galactosemia",
                "normalised_name": "galactosemia",
                "status": "suspected",
                "span": get_span(note, "galactosemia"),
                "icd_code": "E74.21",
            },
            {
                "name_as_written": "ventricular septal defect",
                "normalised_name": "ventricular septal defect",
                "status": "suspected",
                "span": get_span(note, "ventricular septal defect"),
                "icd_code": "Q21.0",
            },
        ],
        "medications": [
            {
                "name": "ampicillin",
                "dose": None,
                "route": "IM",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "ampicillin"),
            },
            {
                "name": "oxygen",
                "dose": "1 liter",
                "route": "nasal cannula",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "oxygen"),
            },
        ],
        "procedures": [
            {
                "name": "C-section",
                "date": None,
                "span": get_span(note, "C-section"),
            },
            {
                "name": "EKG",
                "date": None,
                "span": get_span(note, "EKG"),
            },
            {
                "name": "Phototherapy",
                "date": None,
                "span": get_span(note, "Phototherapy"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "temperature",
                "value": "36.8",
                "unit": "°C",
                "span": get_span(note, "temperature of 36.8"),
            },
            {
                "name": "pulse",
                "value": "148",
                "unit": "bpm",
                "span": get_span(note, "pulse of 148"),
            },
            {
                "name": "respirations",
                "value": "50",
                "unit": "breaths/min",
                "span": get_span(note, "respirations 50"),
            },
            {
                "name": "oxygen saturation",
                "value": "96",
                "unit": "%",
                "span": get_span(note, "oxygen saturation is 96"),
            },
            {
                "name": "Birth weight",
                "value": "8 pounds 6 ounces",
                "unit": None,
                "span": get_span(note, "8 pounds 6 ounces"),
            },
        ],
    }


# ============================================================
# NOTE 071 — Endocrinology
# ============================================================
def build_note_071():
    note = (DATA_DIR / "note_071.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_071",
        "specialty": "Endocrinology",
        "source_row_index": 3791,
        "diagnoses": [
            {
                "name_as_written": "Thyroid goiter",
                "normalised_name": "thyroid goiter",
                "status": "active",
                "span": get_span(note, "Thyroid goiter"),
                "icd_code": "E04.9",
            },
            {
                "name_as_written": "Graves disease",
                "normalised_name": "graves disease",
                "status": "historical",
                "span": get_span(note, "Graves disease"),
                "icd_code": "E05.00",
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
            }
        ],
        "procedures": [
            {
                "name": "Total thyroidectomy",
                "date": "09/04/2003",
                "span": get_span(note, "Total thyroidectomy"),
            },
            {
                "name": "General endotracheal anesthesia",
                "date": None,
                "span": get_span(note, "General endotracheal anesthesia"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 072 — Gastroenterology
# ============================================================
def build_note_072():
    note = (DATA_DIR / "note_072.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_072",
        "specialty": "Gastroenterology",
        "source_row_index": 3644,
        "diagnoses": [
            {
                "name_as_written": "Iron deficiency anemia",
                "normalised_name": "iron deficiency anemia",
                "status": "active",
                "span": get_span(note, "Iron deficiency anemia"),
                "icd_code": "D50.9",
            }
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Colonoscopy with terminal ileum examination",
                "date": None,
                "span": get_span(note, "Colonoscopy with terminal ileum examination"),
            }
        ],
        "allergies": [],
        "vitals": [],
    }


def main():
    builders = [
        ("note_058", build_note_058),
        ("note_059", build_note_059),
        ("note_060", build_note_060),
        ("note_061", build_note_061),
        ("note_062", build_note_062),
        ("note_063", build_note_063),
        ("note_064", build_note_064),
        ("note_065", build_note_065),
        ("note_066", build_note_066),
        ("note_067", build_note_067),
        ("note_068", build_note_068),
        ("note_069", build_note_069),
        ("note_070", build_note_070),
        ("note_071", build_note_071),
        ("note_072", build_note_072),
    ]

    all_passed = True
    for note_id, builder in builders:
        data = builder()
        ok = write_and_verify(note_id, data)
        if not ok:
            all_passed = False

    if all_passed:
        print("\nAll 15 notes (058-072) built and verified successfully!")
    else:
        print("\nSome notes had errors!")


if __name__ == "__main__":
    main()
