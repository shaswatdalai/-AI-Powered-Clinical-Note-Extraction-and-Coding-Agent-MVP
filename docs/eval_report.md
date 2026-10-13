# Evaluation Report — Clinical Note Extraction & ICD-10 Coding Agent (MVP)

**Author:** Shaswat Kumar Dalai
**Date:** 13 Oct 2026 (working draft — numbers pending final eval)
**Commit under evaluation:** [to be filled at freeze time]
**Gold standard:** 57 of 100 hand-labelled notes across 15 specialties

---

## 1. Summary

This report documents the accuracy, robustness, and honesty of the Clinical Note Extraction and ICD-10 Coding Agent MVP. The system extracts diagnoses, medications, procedures, allergies, and vitals from free-text clinical notes, maps diagnoses to ICD-10 codes via hybrid retrieval, and verifies every extracted item with an independent second model. Anything that cannot be verified is flagged for human review.

**Headline numbers (57 notes, RAW mode, exact matcher):**

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | 0.686 | 0.758 | 0.720 | 197 | 90 | 63 |
| Medications | 0.697 | 0.791 | 0.741 | 106 | 46 | 28 |
| Procedures | 0.487 | 0.704 | 0.576 | 76 | 80 | 32 |
| Allergies | 1.000 | 1.000 | 1.000 | 8 | 0 | 0 |
| Vitals | 0.431 | 0.378 | 0.403 | 28 | 37 | 46 |

**SOW Section 8.1 targets:**
- Diagnoses F1 ≥ 0.80 → **not met** (0.720, gap −0.080)
- Medications F1 ≥ 0.85 → **not met** (0.741, gap −0.109)

Both are below target on the 57-note sample. Root causes and improvement plan documented in Section 5. The gaps are not uniform; the failure mode is a mix of extractor over-extraction, extractor under-extraction, and gold-extractor naming convention mismatches.

**Allergies caveat:** the 1.000 F1 is on n=8 items. Do not present it as a headline metric. The 57-note gold has only 8 allergy items across 57 notes; this is too small to be meaningful.

**Vitals caveat:** vitals are not graded by SOW Section 8.1 (only diagnoses, medications, procedures). Reported for completeness.

---

## 2. Methodology

### 2.1 Gold standard

- **Source:** 100 notes sampled from `mtsamples.csv`, one per specialty where possible, filtered to exclude fragments under 200 characters.
- **Current size:** 57 notes across 15 specialties. Each specialty has 3–4 notes. SOW Section 3.7 requires ≥100 notes; this is work in progress.
- **Item counts:** 260 diagnoses, 134 medications, 108 procedures, 8 allergies, 74 vitals. Empty-list rates: allergies 50/57 empty, medications 22/57, procedures 12/57, vitals 34/57, diagnoses 4/57.
- **ICD coverage:** 243 of 260 diagnoses carry an `icd_code`. The remaining 17 are forensic/autopsy findings that do not map cleanly to a single ICD-10 code; those will be excluded from ICD accuracy measurement.
- **Labelling rules:** written in `docs/labelling_guidelines.md` (v1.3). Covers diagnosis inclusion/exclusion, status trigger phrases, span conventions for diagnoses, special cases for autopsy and radiology notes.
- **Labelling method:** the first 12 notes were hand-labelled to establish the pattern and refine the guidelines. The remaining notes used an LLM-assisted workflow — the labelling guidelines and note text were passed to an LLM which produced initial labels, and an automated span verifier (`src/utils/verify_gold.py`) checks every span slices correctly.
- **Known limitation:** LLM-assisted labelling may contain errors. A hand spot-check of 15 randomly sampled notes is planned to bound the error rate.
- **Known gap:** the labelling guideline defines a span convention for diagnoses only. Vitals spans in gold use a different convention (span covers the value, e.g. `"124/78"`, not the name `"Blood pressure"`). This was not intentional; it is a documentation gap in the guideline. The matcher now bridges most of this through span-containment, but it is a real inconsistency in the gold.
- **Frozen before tuning:** labels were written before extractor prompt tuning. Once frozen, they were not adjusted to match system output.
- **Duplicate note:** `note_041` is verbatim identical to `note_024` (MTSamples lists the same content under two specialties). This slightly overweights that content. Documented, not fixed.

### 2.2 Matching rules

- **Exact match (default):** same entity type, normalised name equality, and any span overlap. Name equality is required; span overlap is a sanity check that does not require a specific IoU.
- **Partial match (available, not default):** exact name OR canonical-vital equivalence OR token Jaccard ≥ 0.5 OR span overlap OR span containment.
- **Vital abbreviation map:** `BP ↔ Blood pressure`, `HR ↔ Heart rate`, `RR ↔ Respiratory rate`, `Temp ↔ Temperature`, `Wt ↔ Weight`, `Ht ↔ Height`, `SpO2 ↔ Oxygen saturation`. Applied only for vitals.
- **Status check:** an entity counts as status-correct only if the status matches gold. **Not yet measured** (see Section 6).
- **Reported matcher:** the main table uses exact match. Partial-match results are reported for diagnostic contrast in Section 5.

### 2.3 Runs

- **Extractor model:** Qwen 3.8 27B via Groq (free tier), temperature 0.
- **Verifier model:** Gemini 3.5 Flash Lite via Google AI Studio (free tier), temperature 0.
- **Reproducibility:** all LLM responses are cached on disk keyed by `hash(model + system prompt + user prompt template + guardrails fingerprint + note)`. Identical inputs produce identical metrics.
- **Eval command:** `python -m src.eval.run_eval 57 30` (RAW), `... --verify` (VERIFIED).
- **Rate-limit constraint:** the Groq free tier throttles fresh extraction of 57 notes. Runs of 57 fresh notes take 45–90 minutes with retries and pacing, and can fail if the daily cap is hit. This is SOW Section 7.2's "rate limits are part of the engineering problem."

### 2.4 Baselines

Two modes are measured:

- **Raw mode** — extractor output evaluated directly, no verification. This is the naive single-prompt baseline that SOW Section 3.9 requires.
- **Verified mode** — verifier verdicts applied before evaluation. Only SUPPORTED items count.

Reported side by side in Section 3.2.

---

## 3. Results

### 3.1 Aggregate metrics (57 notes, RAW mode, exact matcher)

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | 0.686 | 0.758 | 0.720 | 197 | 90 | 63 |
| Medications | 0.697 | 0.791 | 0.741 | 106 | 46 | 28 |
| Procedures | 0.487 | 0.704 | 0.576 | 76 | 80 | 32 |
| Allergies | 1.000 | 1.000 | 1.000 | 8 | 0 | 0 |
| Vitals | 0.431 | 0.378 | 0.403 | 28 | 37 | 46 |

### 3.2 Raw vs verified comparison

Measured on the same 57 notes. The RAW numbers are from the current matcher. The VERIFIED numbers are from the pre-matcher-fix run (they will be re-measured once the extractor prompt stabilizes).

| Entity | Raw F1 | Verified F1 | Δ (verified − raw) |
|---|---|---|---|
| Diagnoses | 0.720 | 0.729 | +0.009 |
| Medications | 0.741 | 0.717 | −0.024 |
| Procedures | 0.576 | 0.570 | −0.006 |
| Vitals | 0.403 | 0.144 | (unfair comparison; vitals numbers were before the matcher fix) |

**Observation:** the verifier's net effect on aggregate F1 is small. On medications it is slightly negative (tp 103→100, fp 49→45, fn 31→34 — the verifier trades ~4 false positives for ~3 true positives). Its value is at the item level (category-error rejection, e.g. correctly rejecting "loratadine" as a non-prescription) rather than at the corpus level. This inverts the earlier handoff claim that the verifier improves precision on some entities and is documented honestly.

### 3.3 Per-specialty breakdown

_To be filled from the eval script's per-note output._ Highlights the specialty domains where the system is strongest and weakest. Expected weak domains: Autopsy, Radiology (empty gold by guideline), Dentistry (unusual item naming).

---

## 4. Failure analyses

Per SOW Section 8.9, at least three concrete cases where the system performed poorly, with explanations.

### Failure 1 — Diagnoses F1 is below the SOW target (0.720 vs 0.80)

- **Observation:** diagnoses P=0.686, R=0.758, F1=0.720 on 57 notes. Target is ≥0.80.
- **Root cause:** four distinct patterns, none dominant.
  1. **Extractor returns a descriptive phrase where gold has the shorter entity name.** Example from note_023: gold `"sleep apnea"` and `"Morbid obesity"`, extractor `"History of sleep apnea with reversal after 100-pound weight loss."` and `"Morbid obesity with bmi of 39.4."`. Both are the same clinical entity but the strings do not match exactly.
  2. **Name variation with staging.** Example from note_026: gold `"squamous cell carcinoma of his glottic larynx"`, extractor `"T3 squamous cell carcinoma of his glottic larynx"`. The extractor added a staging prefix.
  3. **Recall misses.** 63 gold diagnoses across 57 notes were not found at all. Examples: `"hallucinations"`, `"psychosis"` (note_006), `"heart attack"`, `"hiatal hernia"`, `"polyps"`, `"urinary stress incontinence"` (note_030), `"compression fractures"` (note_032).
  4. **Category errors.** Extractor emits symptoms and lab values the guideline excludes: `"allergies"` as a diagnosis, `"diminished taste"`, `"xerostomia"`, `"BMI is 38.5"`.
- **Evidence:** the FP/FN dump in this run. See `docs/FINDINGS.md` entry "Failure mode taxonomy".
- **Proposed fix:** (a) matcher-side prefix and subset tolerance (would catch #1 and #2); (b) extractor prompt tightening for #4 (Task B — partially attempted); (c) section-by-section extraction or a second extraction pass for #3.

### Failure 2 — Medications F1 is below the SOW target (0.741 vs 0.85)

- **Observation:** medications P=0.697, R=0.791, F1=0.741 on 57 notes. Target is ≥0.85.
- **Root cause:** two distinct patterns.
  1. **Intraoperative drugs extracted as patient medications.** Examples: `lidocaine`, `epinephrine`, `Marcaine`, `Xylocaine`, `Kefzol` — about 12 false positives across the corpus. These are drugs given during a procedure for anesthesia, not medications the patient takes. The guideline does not currently exclude them.
  2. **Recall misses.** 28 gold medications across 57 notes were not found at all. Examples: `Norvasc`, `Lopressor`, `lovastatin`, `citalopram`, `vitamin D`, `Risperdal`, `Levothyroxine`, `Diovan`, `albuterol`, `Advair Diskus`, `Detrol`.
- **Evidence:** the FP/FN dump. See `docs/FINDINGS.md`.
- **Proposed fix:** (a) prompt tightening for intraoperative drugs (Task B — attempted); (b) recall improvement, likely section-by-section extraction or a "second look" pass for the medications section specifically.

### Failure 3 — Procedures precision is weak (0.487)

- **Observation:** procedures P=0.487, R=0.704, F1=0.576. Procedures are not graded by SOW Section 8.1 but are still part of the extraction report.
- **Root cause:** three patterns.
  1. **Extractor over-specifies procedure names.** Example from note_008: gold `"Full-mouth extraction"`, extractor `"Full-mouth extraction of tooth #3,5,6, 7, 8, 9, 10, 11, 12, 13, 14, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 31, and alveoloplasty in all four quadrants"`.
  2. **Lab tests extracted as procedures.** Examples: `CBC`, `Chem-7`, `U/A`, `CEREBROSPINAL FLUID CULTURE AND SENSITIVITY`, `toxicologic analysis`, `PRELIMINARY TOXICOLOGICAL RESULTS`. About 8 false positives.
  3. **Autopsy itself extracted as a procedure.** Example from note_002: extractor returned `"autopsy"` as a procedure; the guideline says procedures are typically empty for autopsy reports.
- **Evidence:** the FP/FN dump. See `docs/FINDINGS.md`.
- **Proposed fix:** (a) prompt tightening for lab tests and autopsies (Task B — attempted); (b) matcher-side tolerance for over-specified names.

### Failure 4 — Vitals extraction is weak (F1 0.403)

- **Observation:** vitals P=0.431, R=0.378, F1=0.403 on 57 notes. Vitals are not graded by SOW Section 8.1 but are reported for completeness.
- **Root cause:** two issues.
  1. **Span convention mismatch between gold and extractor.** Gold spans the value (e.g. `"124/78"`), extractor spans the name (e.g. `"Blood pressure"`). The matcher's span-containment fix bridges most of this but not all.
  2. **Organ weights and non-vital measurements extracted as vitals.** The extractor over-produces vitals in autopsy and radiology reports.
- **Evidence:** the FP/FN dump. See `docs/FINDINGS.md`.
- **Proposed fix:** (a) update the labelling guideline to define a consistent span convention for vitals; (b) prompt tightening to exclude organ weights and non-patient vitals.

### Failure 5 — Verifier disagreements across model versions

- **Observation:** the same input produced different verdicts on Gemini 3.8 Flash vs Gemini 3.5 Flash Lite.
- **Root cause:** ambiguous items — e.g. "loratadine mentioned as a possible alternative" — are interpreted differently by different models.
- **Evidence:** see `docs/FINDINGS.md` entry on the loratadine case.
- **Proposed fix:** more explicit category rules in the verifier prompt; a second verifier pass for ambiguous items.

### Failure 6 — Duplicate note in the source dataset

- **Observation:** `note_041` is a verbatim duplicate of `note_024`.
- **Root cause:** `mtsamples.csv` lists the same note under two specialties.
- **Evidence:** see `docs/FINDINGS.md`.
- **Proposed fix:** deduplicate notes by text hash during selection.

---

## 5. Gap analysis and improvement plan

Ordered by expected impact on the SOW targets.

**For diagnoses (0.720 → 0.80, need +0.080):**
1. **Matcher-side prefix/subset tolerance.** Would catch the `"T3 squamous cell carcinoma..."` vs `"squamous cell carcinoma..."` pattern and the "long descriptive phrase" vs "short named entity" pattern. Estimated +0.02 to +0.04 F1. Cheapest.
2. **Prompt tightening for category errors (Task B).** Would remove ~10 symptom/lab-value false positives. Estimated +0.01 to +0.02.
3. **Recall improvement via section-by-section extraction.** Hardest. Estimated +0.03 to +0.05.

**For medications (0.741 → 0.85, need +0.109):**
1. **Prompt tightening for intraoperative drugs (Task B).** Would remove ~12 false positives. Estimated +0.03 to +0.05.
2. **Recall improvement via section-by-section extraction for the medications section.** Would recover ~28 missed items. Estimated +0.04 to +0.06.
3. **Matcher-side suffix tolerance for "X with Y" name variations.** Example: `"Tylenol"` vs `"Tylenol with Codeine"`. Estimated +0.01 to +0.02.

**For procedures (not graded but reported):**
1. **Prompt tightening for lab tests and autopsies (Task B).** Would remove ~10 false positives.
2. **Matcher-side tolerance for over-specified procedure names.**

**Honest note:** even if all fixes land, the projected diagnoses F1 is 0.78–0.82 and the projected medications F1 is 0.80–0.85. The diagnoses target is reachable; the medications target is at the edge. This should be communicated clearly rather than overpromised.

---

## 6. Flagging analysis

Per SOW Section 3.9 and 8.6, the fraction of flagged items that were genuinely wrong or ambiguous (flagging precision), and the fraction of gold errors that were caught (flagging recall).

_Not yet measured._ Plan:
- For each note, compute: (a) items the verifier rejected or the orchestrator flagged, (b) which of those were FP items in the RAW eval, (c) which of the gold items the extractor missed (FN items).
- Flagging precision = (flagged items that were FP) / (total flagged items).
- Flagging recall = (FN items that the verifier flagged as missed) / (total FN items).

This is a self-contained script on top of the existing eval output. Planned.

---

## 7. Cost and latency

- **Extractor:** 1 LLM call per note, under 5,000 tokens per call.
- **Verifier:** 1 LLM call per note, under 6,000 tokens per call.
- **Median latency:** _to be measured_. The cache means repeated evals are fast; fresh runs are constrained by Groq's rate limit rather than by per-call latency.
- **Free-tier constraints:** Groq's ~8,000 TPM limit is the binding constraint for batch runs. Fresh 57-note runs take 45–90 minutes with retries. Gemini's free tier is more permissive but has shown 503 instability on 3.8 Flash; 3.5 Flash Lite is stable.
- **Model calls per note:** 2 in verified mode (1 extractor + 1 verifier), 1 in raw mode. Reported per-note in the trace viewer once the UI is built.

---

## 8. Limitations

1. **Gold standard is 57/100 and LLM-assisted.** Bounded by the planned hand spot-check of 15 notes. Two real inconsistencies noted: vitals span convention, and one duplicate note.
2. **Diagnoses and medications F1 are below SOW targets.** Documented in Failure Analyses 1 and 2. The gap is real, not a measurement artifact.
3. **Verifier net effect on F1 is small.** Documented in Section 3.2 and Failure 3. The verifier is doing real work at the item level (correct rejections of non-prescriptions, category errors) but the aggregate F1 delta is close to zero.
4. **Vitals and procedures extraction are weak** (F1 0.403 and 0.576 respectively). Documented in Failures 3 and 4.
5. **Free-tier rate limits constrain batch evaluation.** Full fresh runs of 57 notes take 45–90 minutes. The final 100-note eval will need planning.
6. **Status correctness and ICD accuracy are not yet measured.** Both are required by SOW Section 8. Planned as next deliverables.
7. **No adversarial test set yet.** Planned (SOW Section 3.9).
8. **No contradiction test set yet.** Planned (SOW Section 3.9).
9. **No rare-diagnosis test set yet.** Planned (SOW Section 3.9).

---

## 9. Reproducibility

- Commit hash at time of report: _to be filled at freeze time_.
- Eval command: `python -m src.eval.run_eval 57 30` (RAW), `python -m src.eval.run_eval 57 30 --verify` (VERIFIED).
- All LLM responses are cached on disk keyed by `hash(model + system prompt + user prompt template + guardrails fingerprint + note)`. Re-running with the same code produces identical numbers.
- Model IDs and prompt versions are frozen at the commit above.

---

## 10. Conclusion

The pipeline works end-to-end: raw clinical note → structured items with verbatim evidence and character spans → ICD-10 candidates → independent verification → reconciliation → accepted and flagged outputs. Every accepted item carries a span; the schema rejects items without one; the verifier is independent and fails closed.

Accuracy is below the SOW's target for diagnoses (0.720 vs 0.80) and medications (0.741 vs 0.85). The gaps are not uniform and not a single failure mode — they are a mix of extractor over-extraction (intraoperative drugs, lab tests), extractor under-extraction (recall misses), and naming-convention mismatch between extractor and gold. The matcher has been improved once already (vitals F1 0.144 → 0.403). Two targeted prompt changes are pending. Realistically, the diagnoses target is reachable and the medications target is at the edge.

The system's central claim — **every accepted item is provable** — is enforced by design: mandatory spans, verifier independence, and fail-closed behavior at every stage. No item is accepted without evidence. This is the property the SOW emphasizes above raw F1, and it holds.