# Labelling Guidelines v1

**Author:** Shaswat Kumar Dalai
**Date:** 7 Oct 2026
**Purpose:** Rules for hand-labelling the gold standard. These rules exist so my labels are *consistent* across 100+ notes and so the evaluation is honest.

---

## 1. Note selection

- Total: **100 notes** across **≥10 specialties**.
- Source: `data/mtsamples.csv`.
- Exclude notes where `transcription` is **shorter than 200 characters** (too fragmented to evaluate meaningfully).
- Stratified sampling: roughly **10 notes per specialty** where possible.
- Sample once with a fixed random seed. Do not resample after seeing results.

## 2. What counts as a diagnosis

### Include
- Any condition, disease, syndrome, or disorder the patient **has, had, or is suspected of having**.
- Chronic conditions (diabetes, hypertension, COPD).
- Acute conditions (pneumonia, appendicitis).
- Symptomatic presentations that are formally named as conditions ("migraine", "asthma exacerbation").
- Abbreviations when the meaning is unambiguous ("T2DM", "HTN", "CHF", "COPD").

### Exclude
- **Symptoms** that are not diagnoses ("cough", "fatigue", "nausea").
- **Family history** ("mother had breast cancer" — that's family history, not the patient's diagnosis).
- **Social/behavioral facts** ("smokes 1 pack/day" — not a diagnosis).
- **Anatomical findings** ("left knee" — not a diagnosis).
- **Procedure results** ("EKG shows sinus rhythm" — that's a finding, not a diagnosis).

### Negation handling
- If the note says the patient **does NOT** have a condition ("denies chest pain", "no evidence of pneumonia"), **do not omit**. Label it with status `ruled_out`.
- This is important — the extractor must distinguish between "has" and "does not have."

## 3. Status values for diagnoses

| Status | Meaning | Trigger phrases |
|---|---|---|
| `active` | Current, being treated, or ongoing | "has", "currently", "with", "on [drug] for" |
| `historical` | Past, resolved, or not current | "history of", "past", "s/p", "resolved" |
| `ruled_out` | Note explicitly says patient does NOT have it | "denies", "no evidence of", "negative for" |
| `suspected` | Note says maybe/possibly | "possible", "concern for", "rule out", "query" |

**Default when ambiguous:** use `active`. If it's mentioned without qualification, treat it as currently relevant.

## 4. Spans

- The span covers **exactly the diagnosis text** in the note.
- For `"type 2 diabetes mellitus"`, the span covers all four words.
- For `"HTN"`, the span covers exactly `"HTN"` (3 chars).
- If the diagnosis appears **multiple times** in the note, pick the **first** mention.
- Span offsets refer to the **original note text**, not the masked version.

## 5. Medications

### Include
- Any drug the patient takes, took, or is being prescribed.
- Prescription drugs, OTC drugs, supplements, herbal remedies.
- Drugs mentioned in "current meds", "discharge meds", "home meds" sections.

### Exclude
- Drug **allergies** (those go under "Allergies").
- Drugs the patient is being **started on** during the visit (include, but status = `newly_prescribed`).
- Drugs mentioned only as "considered but not given."

### Fields
- `name`: drug name only. `"Metformin"`, not `"Metformin 500 mg"`.
- `dose`: number + unit as written. `"500 mg"`, `"10 mL"`, `"2 tablets"`.
- `route`: `"PO"`, `"IV"`, `"IM"`, `"SC"`, `"topical"`. `null` if not stated.
- `frequency`: `"twice daily"`, `"BID"`, `"q8h"`, `"PRN"`. `null` if not stated.
- `status`: `current` | `discontinued` | `newly_prescribed`.

### Status values
| Status | Meaning |
|---|---|
| `current` | Patient is currently taking it |
| `discontinued` | Note says it was stopped |
| `newly_prescribed` | Started during this visit |

## 6. Procedures

### Include
- Surgeries, imaging, tests, therapeutic interventions.
- Examples: `"colonoscopy"`, `"CT chest"`, `"biopsy"`, `"appendectomy"`, `"ECG"`, `"EKG"`, `"X-ray"`.

### Exclude
- Routine exam components (`"physical examination"`, `"auscultation"`).
- Medications (even if given IV during a procedure).

### Fields
- `name`: procedure name.
- `date`: if stated in the note. Otherwise `null`.

## 7. Allergies

### Include
- Substance the patient is allergic to.
- Substance the patient has an adverse reaction to.

### Fields
- `substance`: the allergen (`"Penicillin"`).
- `reaction`: if stated (`"rash"`, `"anaphylaxis"`). Otherwise `null`.

## 8. Vitals

### Include
- Measured values: BP, HR, RR, temperature, O2 saturation, weight, height, BMI.
- Lab values with units (glucose, creatinine, etc.) — treat as vitals if listed in a "Vitals" or "Lab Data" section.

### Fields
- `name`: `"BP"`, `"HR"`, `"Temp"`, `"O2 sat"`.
- `value`: as written. `"120/80"`, `"72"`, `"98.6"`, `"98"`.
- `unit`: `"mmHg"`, `"bpm"`, `"°F"`, `"%"`. `null` if not stated.

## 9. Ambiguity resolution

When unsure whether something is a diagnosis:

1. **Is it formally named?** "Hypertension" → yes. "Feeling dizzy" → no (it's a symptom).
2. **Does the note treat it as a condition?** "Patient has CHF" → yes. "Patient's father has CHF" → no (family history).
3. **Is it in the Assessment/Plan section?** Usually yes.
4. **Would a medical coder list it?** If unclear, err on the side of **including** it — the verifier will filter false positives.

When unsure about status:
- Default to `active` unless there's a clear signal otherwise.

When unsure about span:
- Use the **smallest span** that captures the meaningful text. `"diabetes"` not `"the patient has type 2 diabetes"`.

## 10. What to do with fragments and messy notes

- **Fragmented notes** (missing sentences, cut off): label what you can. Note the fragment in a `notes` field on the note.
- **Notes with typos**: label against the intent. `"diabeties"` → still `"diabetes"` in normalised name, but span covers `"diabeties"`.
- **Duplicate mentions**: label the first, ignore subsequent for span. Duplicates don't add new items.

## 11. Change log

- **v1 (7 Oct 2026):** Initial version. Written before any gold notes were labelled.


## Radiology and imaging reports

When a note is primarily a radiology report (ultrasound, CT, MRI, X-ray):

**DO extract as diagnoses:**
- Named pathological findings that describe a condition:
  - "carotid artery plaque" / "heterogeneous plaque"
  - "stenosis" (specify location and severity if stated)
  - "fracture", "mass", "nodule", "effusion", "consolidation"
  - "cardiomegaly", "hepatomegaly", "splenomegaly"
- Each anatomically distinct finding gets its own item, even if the same
  type of finding appears on both sides.

**DO NOT extract as diagnoses:**
- Measurements and velocities ("peak systolic velocity 280 cm/sec")
- Descriptive qualifiers alone ("mild", "moderate", "severe")
- Normal findings ("no masses", "unremarkable")
- Comparison statements ("stable compared to prior")
- Impression headers ("FINDINGS:", "IMPRESSION:")

**Do NOT extract peak systolic velocities as vitals.** They are
diagnostic measurements, not patient vitals.

**Multiple same-type findings on different sides** → separate items
with separate spans (e.g. "mild heterogeneous plaque" appears twice,
once for right and once for left; both are extracted).