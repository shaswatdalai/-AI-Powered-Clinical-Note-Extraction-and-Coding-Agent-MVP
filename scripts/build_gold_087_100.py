"""
Build gold/note_087.json through gold/note_100.json.
Run from project root: python scripts/build_gold_087_100.py
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
# NOTE 087 — Pediatrics - Neonatal
# ============================================================
def build_note_087():
    note = (DATA_DIR / "note_087.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_087",
        "specialty": "Pediatrics - Neonatal",
        "source_row_index": 1896,
        "diagnoses": [
            {
                "name_as_written": "rectal bleeding",
                "normalised_name": "rectal bleeding",
                "status": "active",
                "span": get_span(note, "rectal bleeding"),
                "icd_code": "K62.5",
            },
        ],
        "medications": [
            {
                "name": "Zantac",
                "dose": None,
                "route": "IV",
                "frequency": None,
                "status": "current",
                "span": get_span(note, "IV Zantac"),
            },
        ],
        "procedures": [
            {
                "name": "CT scan of the abdomen",
                "date": None,
                "span": get_span(note, "CT scan of the abdomen"),
            },
            {
                "name": "Meckel scan",
                "date": None,
                "span": get_span(note, "Meckel scan"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "Temperature",
                "value": "99.5",
                "unit": "°F",
                "span": get_span(note, "Temperature 99.5 degrees Fahrenheit"),
            },
            {
                "name": "pulse",
                "value": "142",
                "unit": "per minute",
                "span": get_span(note, "pulse 142 per minute"),
            },
            {
                "name": "respirations",
                "value": "28",
                "unit": "per minute",
                "span": get_span(note, "respirations 28 per minute"),
            },
            {
                "name": "Weight",
                "value": "9.6",
                "unit": "kilogram",
                "span": get_span(note, "Weight 9.6 kilogram"),
            },
        ],
    }


# ============================================================
# NOTE 088 — Physical Medicine - Rehab
# ============================================================
def build_note_088():
    note = (DATA_DIR / "note_088.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_088",
        "specialty": "Physical Medicine - Rehab",
        "source_row_index": 1875,
        "diagnoses": [
            {
                "name_as_written": "rheumatoid arthritis",
                "normalised_name": "rheumatoid arthritis",
                "status": "active",
                "span": get_span(note, "rheumatoid arthritis"),
                "icd_code": "M06.9",
            },
            {
                "name_as_written": "fibromyalgia",
                "normalised_name": "fibromyalgia",
                "status": "active",
                "span": get_span(note, "fibromyalgia"),
                "icd_code": "M79.7",
            },
            {
                "name_as_written": "hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "hypercholesterolemia",
                "normalised_name": "hypercholesterolemia",
                "status": "active",
                "span": get_span(note, "hypercholesterolemia"),
                "icd_code": "E78.00",
            },
            {
                "name_as_written": "irritable bowel syndrome",
                "normalised_name": "irritable bowel syndrome",
                "status": "active",
                "span": get_span(note, "irritable bowel syndrome"),
                "icd_code": "K58.9",
            },
            {
                "name_as_written": "right C8/T1 radiculopathy",
                "normalised_name": "cervical radiculopathy C8-T1",
                "status": "active",
                "span": get_span(note, "right C8/T1 radiculopathy"),
                "icd_code": "M54.12",
            },
            {
                "name_as_written": "right C6/C7 radiculopathy",
                "normalised_name": "cervical radiculopathy C6-C7",
                "status": "active",
                "span": get_span(note, "right C6/C7 radiculopathy"),
                "icd_code": "M54.12",
            },
            {
                "name_as_written": "chronic left C8/T1 denervation",
                "normalised_name": "chronic cervical denervation C8-T1, left",
                "status": "active",
                "span": get_span(note, "chronic left C8/T1 denervation"),
                "icd_code": "G54.2",
            },
            {
                "name_as_written": "lumbosacral radiculopathies",
                "normalised_name": "lumbosacral radiculopathy",
                "status": "active",
                "span": get_span(note, "lumbosacral radiculopathies"),
                "icd_code": "M54.17",
            },
            {
                "name_as_written": "sensory carpal tunnel",
                "normalised_name": "carpal tunnel syndrome",
                "status": "active",
                "span": get_span(note, "sensory carpal tunnel"),
                "icd_code": "G56.00",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "bilateral carpal tunnel release",
                "date": None,
                "span": get_span(note, "bilateral carpal tunnel release"),
            },
            {
                "name": "Nerve conduction studies",
                "date": None,
                "span": get_span(note, "NERVE CONDUCTION STUDIES"),
            },
            {
                "name": "Needle EMG",
                "date": None,
                "span": get_span(note, "Needle EMG"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 089 — Podiatry
# ============================================================
def build_note_089():
    note = (DATA_DIR / "note_089.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_089",
        "specialty": "Podiatry",
        "source_row_index": 1817,
        "diagnoses": [
            {
                "name_as_written": "Plantar fascitis",
                "normalised_name": "plantar fasciitis",
                "status": "active",
                "span": get_span(note, "Plantar fascitis"),
                "icd_code": "M72.2",
            },
            {
                "name_as_written": "heel spur syndrome",
                "normalised_name": "heel spur",
                "status": "active",
                "span": get_span(note, "heel spur syndrome"),
                "icd_code": "M77.30",
            },
        ],
        "medications": [
            {
                "name": "lidocaine",
                "dose": "3 cc 2:1 mixture of 1% lidocaine plain with dexamethasone phospate",
                "route": "injection",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "lidocaine plain with dexamethasone phospate"),
            },
            {
                "name": "dexamethasone",
                "dose": None,
                "route": "injection",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "dexamethasone phospate"),
            },
        ],
        "procedures": [],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 090 — Psychiatry / Psychology
# (Only formal diagnoses; do NOT extract symptoms like "anxious"
#  or "flat affect")
# ============================================================
def build_note_090():
    note = (DATA_DIR / "note_090.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_090",
        "specialty": "Psychiatry / Psychology",
        "source_row_index": 1804,
        "diagnoses": [
            {
                "name_as_written": "depression",
                "normalised_name": "major depressive disorder",
                "status": "active",
                "span": get_span(note, "depression"),
                "icd_code": "F32.9",
            },
            {
                "name_as_written": "Hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "Hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "Hypercholesterolemia",
                "normalised_name": "hypercholesterolemia",
                "status": "active",
                "span": get_span(note, "Hypercholesterolemia"),
                "icd_code": "E78.00",
            },
            {
                "name_as_written": "Coronary artery disease",
                "normalised_name": "coronary artery disease",
                "status": "active",
                "span": get_span(note, "Coronary artery disease"),
                "icd_code": "I25.10",
            },
            {
                "name_as_written": "Osteoarthritis",
                "normalised_name": "osteoarthritis",
                "status": "active",
                "span": get_span(note, "Osteoarthritis"),
                "icd_code": "M19.90",
            },
            {
                "name_as_written": "Chronic obstructive pulmonary disease",
                "normalised_name": "chronic obstructive pulmonary disease",
                "status": "active",
                "span": get_span(note, "Chronic obstructive pulmonary disease"),
                "icd_code": "J44.1",
            },
            {
                "name_as_written": "Hypothyroidism",
                "normalised_name": "hypothyroidism",
                "status": "active",
                "span": get_span(note, "Hypothyroidism"),
                "icd_code": "E03.9",
            },
        ],
        "medications": [
            {
                "name": "Tylenol",
                "dose": "650 mg",
                "route": None,
                "frequency": "q.6h. p.r.n.",
                "status": "current",
                "span": get_span(note, "Tylenol"),
            },
            {
                "name": "Xanax",
                "dose": "0.5",
                "route": None,
                "frequency": "q.4h. p.r.n.",
                "status": "current",
                "span": get_span(note, "Xanax"),
            },
            {
                "name": "Lasix",
                "dose": "80 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Lasix"),
            },
            {
                "name": "Isordil",
                "dose": "10 mg",
                "route": None,
                "frequency": "t.i.d.",
                "status": "current",
                "span": get_span(note, "Isordil"),
            },
            {
                "name": "KCl",
                "dose": "20 mEq",
                "route": None,
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "KCl"),
            },
            {
                "name": "lactulose",
                "dose": "10 g",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "lactulose"),
            },
            {
                "name": "Cozaar",
                "dose": "50 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Cozaar"),
            },
            {
                "name": "Synthroid",
                "dose": "75 mcg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Synthroid"),
            },
            {
                "name": "Singulair",
                "dose": "10 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Singulair"),
            },
            {
                "name": "Lumigan",
                "dose": "one drop both eyes",
                "route": "ophthalmic",
                "frequency": "at bed time",
                "status": "current",
                "span": get_span(note, "Lumigan"),
            },
            {
                "name": "NitroQuick",
                "dose": None,
                "route": None,
                "frequency": "p.r.n.",
                "status": "current",
                "span": get_span(note, "NitroQuick"),
            },
            {
                "name": "Pravachol",
                "dose": "20 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Pravachol"),
            },
            {
                "name": "Feldene",
                "dose": "20 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Feldene"),
            },
            {
                "name": "Paxil",
                "dose": "20 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Paxil"),
            },
            {
                "name": "Minipress",
                "dose": "2 mg",
                "route": None,
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Minipress"),
            },
            {
                "name": "Provera",
                "dose": None,
                "route": None,
                "frequency": "p.r.n.",
                "status": "current",
                "span": get_span(note, "Provera"),
            },
            {
                "name": "Advair",
                "dose": "250/50",
                "route": "inhalation",
                "frequency": "one puff b.i.d.",
                "status": "current",
                "span": get_span(note, "Advair"),
            },
            {
                "name": "Senokot",
                "dose": "one tablet",
                "route": None,
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "Senokot"),
            },
            {
                "name": "Timoptic",
                "dose": "one drop OU",
                "route": "ophthalmic",
                "frequency": "daily",
                "status": "current",
                "span": get_span(note, "Timoptic"),
            },
            {
                "name": "verapamil",
                "dose": "80 mg",
                "route": None,
                "frequency": "b.i.d.",
                "status": "current",
                "span": get_span(note, "verapamil"),
            },
            {
                "name": "Darvocet",
                "dose": None,
                "route": None,
                "frequency": None,
                "status": "current",
                "span": get_span(note, "Darvocet"),
            },
        ],
        "procedures": [
            {
                "name": "psychiatric evaluation",
                "date": None,
                "span": get_span(note, "psychiatric evaluation"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 091 — Radiology
# (Only named pathological findings. No measurements, velocities,
#  or normal findings.)
# ============================================================
def build_note_091():
    note = (DATA_DIR / "note_091.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_091",
        "specialty": "Radiology",
        "source_row_index": 1611,
        "diagnoses": [
            {
                "name_as_written": "split tear of the peroneus brevis tendon",
                "normalised_name": "peroneus brevis tendon tear",
                "status": "active",
                "span": get_span(note, "split tear of the peroneus brevis tendon"),
                "icd_code": "S86.312A",
            },
            {
                "name_as_written": "synovitis of the peroneus longus tendon sheath",
                "normalised_name": "peroneal tendon sheath synovitis",
                "status": "active",
                "span": get_span(note, "synovitis of the peroneus longus tendon sheath"),
                "icd_code": "M65.879",
            },
            {
                "name_as_written": "tenosynovitis of the posterior tibialis tendon sheath",
                "normalised_name": "posterior tibialis tenosynovitis",
                "status": "active",
                "span": get_span(note, "tenosynovitis of the posterior tibialis tendon sheath"),
                "icd_code": "M65.879",
            },
            {
                "name_as_written": "tenosynovitis of the Achilles tendon",
                "normalised_name": "achilles tendinosis",
                "status": "active",
                "span": get_span(note, "tenosynovitis of the Achilles tendon"),
                "icd_code": "M76.60",
            },
            {
                "name_as_written": "plantar calcaneal spur",
                "normalised_name": "plantar calcaneal spur",
                "status": "active",
                "span": get_span(note, "plantar calcaneal spur"),
                "icd_code": "M77.30",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "MRI RIGHT ANKLE",
                "date": None,
                "span": get_span(note, "MRI RIGHT ANKLE"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 092 — Rheumatology
# ============================================================
def build_note_092():
    note = (DATA_DIR / "note_092.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_092",
        "specialty": "Rheumatology",
        "source_row_index": 1480,
        "diagnoses": [
            {
                "name_as_written": "rheumatoid arthritis",
                "normalised_name": "rheumatoid arthritis",
                "status": "active",
                "span": get_span(note, "rheumatoid arthritis"),
                "icd_code": "M06.9",
            },
            {
                "name_as_written": "hypertension",
                "normalised_name": "hypertension",
                "status": "active",
                "span": get_span(note, "hypertension"),
                "icd_code": "I10",
            },
            {
                "name_as_written": "peripheral vascular disease",
                "normalised_name": "peripheral vascular disease",
                "status": "active",
                "span": get_span(note, "peripheral vascular disease"),
                "icd_code": "I73.9",
            },
        ],
        "medications": [
            {
                "name": "prednisone",
                "dose": "5 mg",
                "route": None,
                "frequency": "a day",
                "status": "current",
                "span": get_span(note, "prednisone"),
            },
        ],
        "procedures": [
            {
                "name": "left BKA",
                "date": None,
                "span": get_span(note, "left BKA"),
            },
        ],
        "allergies": [],
        "vitals": [
            {
                "name": "BP",
                "value": "130/70",
                "unit": "mmHg",
                "span": get_span(note, "BP 130/70"),
            },
            {
                "name": "heart rate",
                "value": "80",
                "unit": "bpm",
                "span": get_span(note, "heart rate 80"),
            },
            {
                "name": "respiratory rate",
                "value": "14",
                "unit": "breaths/min",
                "span": get_span(note, "respiratory rate 14"),
            },
        ],
    }


# ============================================================
# NOTE 093 — SOAP / Chart / Progress Notes
# ============================================================
def build_note_093():
    note = (DATA_DIR / "note_093.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_093",
        "specialty": "SOAP / Chart / Progress Notes",
        "source_row_index": 1409,
        "diagnoses": [],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [
            {
                "name": "weight",
                "value": "186-1/2",
                "unit": "pounds",
                "span": get_span(note, "186-1/2 pounds"),
            },
        ],
    }


# ============================================================
# NOTE 094 — Sleep Medicine
# ============================================================
def build_note_094():
    note = (DATA_DIR / "note_094.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_094",
        "specialty": "Sleep Medicine",
        "source_row_index": 1458,
        "diagnoses": [
            {
                "name_as_written": "epilepsy",
                "normalised_name": "epilepsy",
                "status": "active",
                "span": get_span(note, "epilepsy"),
                "icd_code": "G40.909",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Video EEG monitoring",
                "date": None,
                "span": get_span(note, "Video EEG monitoring"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 095 — Speech - Language
# ============================================================
def build_note_095():
    note = (DATA_DIR / "note_095.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_095",
        "specialty": "Speech - Language",
        "source_row_index": 1285,
        "diagnoses": [
            {
                "name_as_written": "brain tumor",
                "normalised_name": "brain neoplasm",
                "status": "active",
                "span": get_span(note, "brain tumor"),
                "icd_code": "D49.6",
            },
            {
                "name_as_written": "breast cancer",
                "normalised_name": "breast cancer",
                "status": "active",
                "span": get_span(note, "breast cancer"),
                "icd_code": "C50.919",
            },
            {
                "name_as_written": "left-sided weakness",
                "normalised_name": "left hemiparesis",
                "status": "active",
                "span": get_span(note, "left-sided weakness"),
                "icd_code": "G81.90",
            },
            {
                "name_as_written": "cognitive linguistic deficits",
                "normalised_name": "cognitive communication deficit",
                "status": "active",
                "span": get_span(note, "cognitive linguistic deficits"),
                "icd_code": "R41.840",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "brain tumor removed",
                "date": "10/24/08",
                "span": get_span(note, "brain tumor removed"),
            },
            {
                "name": "second surgery was performed to reduce the swelling",
                "date": None,
                "span": get_span(note, "second surgery was performed to reduce the swelling"),
            },
            {
                "name": "radiation therapy",
                "date": None,
                "span": get_span(note, "radiation therapy"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 096 — Surgery
# ============================================================
def build_note_096():
    note = (DATA_DIR / "note_096.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_096",
        "specialty": "Surgery",
        "source_row_index": 229,
        "diagnoses": [
            {
                "name_as_written": "upper abdominal wall skin mass",
                "normalised_name": "skin mass of upper abdominal wall",
                "status": "active",
                "span": get_span(note, "upper abdominal wall skin mass"),
                "icd_code": "R22.2",
            },
        ],
        "medications": [
            {
                "name": "Marcaine",
                "dose": "10 mL",
                "route": "injection",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Marcaine"),
            },
        ],
        "procedures": [
            {
                "name": "Postpartum tubal ligation",
                "date": None,
                "span": get_span(note, "Postpartum tubal ligation"),
            },
            {
                "name": "removal of upper abdominal skin wall mass",
                "date": None,
                "span": get_span(note, "removal of upper abdominal skin wall mass"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 097 — Urology
# ============================================================
def build_note_097():
    note = (DATA_DIR / "note_097.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_097",
        "specialty": "Urology",
        "source_row_index": 158,
        "diagnoses": [
            {
                "name_as_written": "Phimosis",
                "normalised_name": "phimosis",
                "status": "active",
                "span": get_span(note, "Phimosis"),
                "icd_code": "N47.1",
            },
            {
                "name_as_written": "adhesions",
                "normalised_name": "penile adhesions",
                "status": "active",
                "span": get_span(note, "adhesions"),
                "icd_code": "N47.5",
            },
            {
                "name_as_written": "ventral chordee",
                "normalised_name": "chordee",
                "status": "active",
                "span": get_span(note, "ventral chordee"),
                "icd_code": "N48.89",
            },
        ],
        "medications": [
            {
                "name": "Marcaine",
                "dose": None,
                "route": "injection",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "Marcaine"),
            },
            {
                "name": "lidocaine",
                "dose": None,
                "route": "injection",
                "frequency": None,
                "status": "newly_prescribed",
                "span": get_span(note, "lidocaine"),
            },
        ],
        "procedures": [
            {
                "name": "Circumcision",
                "date": None,
                "span": get_span(note, "Circumcision"),
            },
            {
                "name": "release of ventral chordee",
                "date": None,
                "span": get_span(note, "release of ventral chordee"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 098 — Radiology
# (Same radiology rules as note_091: only named pathological
#  findings. No measurements, velocities, or normal findings.
#  Empty extraction is valid for normal-only reports.)
# ============================================================
def build_note_098():
    note = (DATA_DIR / "note_098.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_098",
        "specialty": "Radiology",
        "source_row_index": 1491,
        "diagnoses": [
            {
                "name_as_written": "intrauterine pregnancy",
                "normalised_name": "intrauterine pregnancy",
                "status": "active",
                "span": get_span(note, "intrauterine pregnancy"),
                "icd_code": "Z33.1",
            },
            {
                "name_as_written": "inevitable abortion",
                "normalised_name": "threatened abortion",
                "status": "suspected",
                "span": get_span(note, "inevitable abortion"),
                "icd_code": "O03.9",
            },
        ],
        "medications": [],
        "procedures": [],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 099 — Nephrology
# ============================================================
def build_note_099():
    note = (DATA_DIR / "note_099.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_099",
        "specialty": "Nephrology",
        "source_row_index": 3019,
        "diagnoses": [
            {
                "name_as_written": "Right renal mass",
                "normalised_name": "renal mass",
                "status": "active",
                "span": get_span(note, "Right renal mass"),
                "icd_code": "N28.89",
            },
            {
                "name_as_written": "Hematuria",
                "normalised_name": "hematuria",
                "status": "active",
                "span": get_span(note, "Hematuria"),
                "icd_code": "R31.9",
            },
            {
                "name_as_written": "Right ureteropelvic junction obstruction",
                "normalised_name": "ureteropelvic junction obstruction",
                "status": "active",
                "span": get_span(note, "Right ureteropelvic junction obstruction"),
                "icd_code": "N13.1",
            },
            {
                "name_as_written": "hypospadias",
                "normalised_name": "hypospadias",
                "status": "active",
                "span": get_span(note, "hypospadias"),
                "icd_code": "Q54.9",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Cystourethroscopy",
                "date": None,
                "span": get_span(note, "Cystourethroscopy"),
            },
            {
                "name": "Right retrograde pyelogram",
                "date": None,
                "span": get_span(note, "Right retrograde pyelogram"),
            },
            {
                "name": "Right ureteral pyeloscopy",
                "date": None,
                "span": get_span(note, "Right ureteral pyeloscopy"),
            },
            {
                "name": "Right renal biopsy",
                "date": None,
                "span": get_span(note, "Right renal biopsy"),
            },
            {
                "name": "Right double-J 4.5 x 26 mm ureteral stent placement",
                "date": None,
                "span": get_span(note, "Right double-J 4.5 x 26 mm ureteral stent placement"),
            },
            {
                "name": "echocardiogram",
                "date": None,
                "span": get_span(note, "echocardiogram"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


# ============================================================
# NOTE 100 — Surgery
# ============================================================
def build_note_100():
    note = (DATA_DIR / "note_100.txt").read_text(encoding="utf-8")
    return {
        "note_id": "note_100",
        "specialty": "Surgery",
        "source_row_index": 819,
        "diagnoses": [
            {
                "name_as_written": "Right flank subcutaneous mass",
                "normalised_name": "subcutaneous mass of right flank",
                "status": "active",
                "span": get_span(note, "Right flank subcutaneous mass"),
                "icd_code": "R22.2",
            },
        ],
        "medications": [],
        "procedures": [
            {
                "name": "Excision of soft tissue mass on the right flank",
                "date": None,
                "span": get_span(note, "Excision of soft tissue mass on the right flank"),
            },
        ],
        "allergies": [],
        "vitals": [],
    }


def main():
    builders = [
        ("note_087", build_note_087),
        ("note_088", build_note_088),
        ("note_089", build_note_089),
        ("note_090", build_note_090),
        ("note_091", build_note_091),
        ("note_092", build_note_092),
        ("note_093", build_note_093),
        ("note_094", build_note_094),
        ("note_095", build_note_095),
        ("note_096", build_note_096),
        ("note_097", build_note_097),
        ("note_098", build_note_098),
        ("note_099", build_note_099),
        ("note_100", build_note_100),
    ]

    all_passed = True
    for note_id, builder in builders:
        data = builder()
        ok = write_and_verify(note_id, data)
        if not ok:
            all_passed = False

    if all_passed:
        print("\nAll 14 notes (087-100) built and verified successfully!")
    else:
        print("\nSome notes had errors!")


if __name__ == "__main__":
    main()
