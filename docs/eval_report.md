# Evaluation Report — Clinical Note Extraction & ICD-10 Coding Agent (MVP)

**Author:** Shaswat Kumar Dalai
**Date:** 14 Oct 2026 (working draft — headline numbers pending final eval run)
**Commit under evaluation:** [to be filled at freeze time]
**Gold standard:** **100 of 100 hand-labelled notes across 26 specialties**

---

## 1. Summary

This report documents the accuracy, robustness, and honesty of the Clinical Note Extraction and ICD-10 Coding Agent MVP. The system extracts diagnoses, medications, procedures, allergies, and vitals from free-text clinical notes, maps diagnoses to ICD-10 codes via hybrid retrieval, and verifies every extracted item with an independent second model. Anything that cannot be verified is flagged for human review.

**Headline numbers (100 notes, RAW mode, exact matcher):**

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | _pending_ | _pending_ | _pending_ | | | |
| Medications | _pending_ | _pending_ | _pending_ | | | |
| Procedures | _pending_ | _pending_ | _pending_ | | | |
| Allergies | _pending_ | _pending_ | _pending_ | | | |
| Vitals | _pending_ | _pending_ | _pending_ | | | |

**Prior baseline (57 notes, RAW mode, exact matcher):**

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | 0.686 | 0.758 | 0.720 | 197 | 90 | 63 |
| Medications | 0.697 | 0.791 | 0.741 | 106 | 46 | 28 |
| Procedures | 0.487 | 0.704 | 0.576 | 76 | 80 | 32 |
| Allergies | 1.000 | 1.000 | 1.000 | 8 | 0 | 0 |
| Vitals | 0.431 | 0.378 | 0.403 | 28 | 37 | 46 |

**SOW Section 8.1 targets:**
- Diagnoses F1 ≥ 0.80 → _pending on 100-note run_
- Medications F1 ≥ 0.85 → _pending on 100-note run_

On the 57-note baseline both were below target (0.720 and 0.741). Task B and Task C prompt changes have been applied since; the 100-note run will show whether the gap closes. Root causes and improvement plan are documented in Section 5.

**Allergies caveat:** allergy F1 is measured on very small n (8 items on the 57-note baseline; the 100-note set will add a handful more). Do not present it as a headline metric — it is reported for completeness.

**Vitals caveat:** vitals are not graded by SOW Section 8.1 (only diagnoses, medications, procedures). Reported for completeness.

---

## 2. Methodology

### 2.1 Gold standard

- **Source:** notes sampled from `mtsamples.csv`, one per specialty where possible, filtered to exclude fragments under 200 characters.
- **Current size:** **100 notes across 26 specialties.** SOW Section 3.7 requires ≥100 notes and ≥10 specialties; both targets are met.
- **Item counts:** _to be measured on the full 100-note set._ Baseline on 57 notes was 260 diagnoses, 134 medications, 108 procedures, 8 allergies, 74 vitals.
- **ICD coverage:** _to be measured on the 100-note set._ Baseline: 243 of 260 diagnoses carried an `icd_code`.
- **Labelling rules:** written in `docs/labelling_guidelines.md` (v1.3). Covers diagnosis inclusion/exclusion, status trigger phrases, span conventions for diagnoses, special cases for autopsy and radiology notes.
- **Labelling method:** the first 12 notes were hand-labelled to establish the pattern and refine the guidelines. Notes 013–100 used a structured LLM-assisted workflow with hand review of each file; the build scripts (`scripts/build_gold_*.py`) are committed to the repository. `src/utils/verify_gold.py` validates every span in every gold file and exits non-zero on any mismatch.
- **Known limitation:** LLM-assisted labelling may contain errors. A hand spot-check of 15 randomly sampled notes is planned to bound the error rate.
- **Known gap:** the labelling guideline defines a span convention for diagnoses only. Vitals spans in gold use a different convention (span covers the value, e.g. `"124/78"`, not the name `"Blood pressure"`). This was not intentional; it is a documentation gap in the guideline. The matcher bridges most of this through span-containment, but it is a real inconsistency in the gold.
- **Frozen before tuning:** labels were written before extractor prompt tuning. Once frozen, they were not adjusted to match system output.
- **Duplicate note:** `note_041` is verbatim identical to `note_024` (MTSamples lists the same content under two specialties). This slightly overweights that content. Documented, not fixed.

### 2.2 Matching rules

- **Exact match (default):** same entity type, normalised name equality, and any span overlap. Name equality is required; span overlap is a sanity check that does not require a specific IoU.
- **Partial match (available, not default):** exact name OR canonical-vital equivalence OR token Jaccard ≥ 0.5 OR span overlap OR span containment.
- **Vital abbreviation map:** `BP ↔ Blood pressure`, `HR ↔ Heart rate`, `RR ↔ Respiratory rate`, `Temp ↔ Temperature`, `Wt ↔ Weight`, `Ht ↔ Height`, `SpO2 ↔ Oxygen saturation`. Applied only for vitals.
- **Status check:** an entity counts as status-correct only if the status matches gold. Measured separately in `src/eval/status_eval.py` (see Section 3.6).
- **Reported matcher:** the main table uses exact match. Partial-match results are reported for diagnostic contrast in Section 5.

### 2.3 Runs

- **Extractor model:** Qwen 3.8 27B via Groq (free tier), temperature 0.
- **Verifier model:** Gemini 3.5 Flash Lite via Google AI Studio (free tier), temperature 0.
- **Reproducibility:** all LLM responses are cached on disk keyed by `hash(model + system prompt + user prompt template + guardrails fingerprint + note)`. Identical inputs produce identical metrics.
- **Eval command:** `python -m src.eval.run_eval 100 60` (RAW), `... --verify` (VERIFIED).
- **Rate-limit constraint:** the Groq free tier throttles fresh extraction. Full fresh runs of 100 notes take 60–120 minutes with retries and pacing, and can fail if the daily cap is hit. This is SOW Section 7.2's "rate limits are part of the engineering problem."

### 2.4 Baselines

Two modes are measured:

- **Raw mode** — extractor output evaluated directly, no verification. This is the naive single-prompt baseline that SOW Section 3.9 requires.
- **Verified mode** — verifier verdicts applied before evaluation. Only SUPPORTED items count.

Reported side by side in Section 3.2.

---

## 3. Results

### 3.1 Aggregate metrics (100 notes, RAW mode, exact matcher)

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | _pending_ | _pending_ | _pending_ | | | |
| Medications | _pending_ | _pending_ | _pending_ | | | |
| Procedures | _pending_ | _pending_ | _pending_ | | | |
| Allergies | _pending_ | _pending_ | _pending_ | | | |
| Vitals | _pending_ | _pending_ | _pending_ | | | |

### 3.2 Raw vs verified comparison

Measured on the same 100 notes. Both columns will be filled from the same
run to ensure a fair comparison (the matcher and prompt are frozen at the
commit under evaluation).

| Entity | Raw F1 | Verified F1 | Δ (verified − raw) |
|---|---|---|---|
| Diagnoses | _pending_ | _pending_ | _pending_ |
| Medications | _pending_ | _pending_ | _pending_ |
| Procedures | _pending_ | _pending_ | _pending_ |
| Vitals | _pending_ | _pending_ | _pending_ |

**Prior observation (57-note baseline):** the verifier's net effect on
aggregate F1 was small. On medications it was slightly negative (tp 103→100,
fp 49→45, fn 31→34 — the verifier trades ~4 false positives for ~3 true
positives). Its value is at the item level (category-error rejection,
e.g. correctly rejecting "loratadine" as a non-prescription) rather than
at the corpus level. This inverts an earlier handoff assumption that the
verifier improves precision on some entities and is documented honestly.

### 3.3 Per-specialty breakdown

_To be filled from the eval script's per-note output._ The 100-note set
covers 26 specialties including several added in notes 087–100:
Pediatrics - Neonatal, Physical Medicine - Rehab, Podiatry,
Psychiatry / Psychology, Rheumatology, SOAP / Chart / Progress Notes,
Sleep Medicine, Speech - Language, Urology, Nephrology. Expected weak
domains: Autopsy (special handling), Radiology (empty gold by
guideline), Psychiatry (formal-diagnosis-only rule).

### 3.4 Span faithfulness (SOW 8.2)

**Target:** 100% of accepted items have a span that exists at the stated
offsets and supports the item.

**Result on notes 001–020:** **193/193 = 1.000** (after the token-overlap
and quote-containment fallbacks described in FINDINGS, 2026-10-13).

**Strict verbatim-only measurement:** 192/193 = 0.995. The single
deviation is `note_020`, procedure `p8`, where the extractor returned
`"composite restoration"` over the slice `"tooth C, M, L, S composite"`.
The word "restoration" is not in the source note. The verifier accepted
the item because the composite material is documented.

**Interpretation.** Under the SOW's literal "supports the item" wording,
this is a partial-support case. Under the labelling guideline's rule 9
("use the smallest span that captures the meaningful text"), it is
defensible. We report both numbers and document the deviation rather
than conceal it under a relaxed check.

**Full-corpus result:** _to be re-measured on all 100 notes._

### 3.5 Rare-diagnosis abstention (SOW 8.4b)

**Target:** ≥ 0.80 correct NO_CONFIDENT_MATCH on the 10-note
rare-diagnosis set.

**Set construction.** 10 notes chosen by hand from 27 candidates. Common
diagnoses (`hypertension`, `obesity`, `peptic ulcer disease`, `polyps`,
`cancer`) that the ICD gate was incorrectly rejecting were excluded —
those are gate bugs, not genuine rare-diagnosis cases. The 10 included
notes contain 12 rare diagnoses across forensic, bariatric,
chiropractic, ENT, cosmetic, dermatology, dental, emergency, and
gastroenterology specialties.

**First run:** **8/8 = 1.000** on executed items (three notes skipped on
Groq 429s). Re-run required to get the full 12-item denominator.

**Interpretation.** The confidence gate correctly abstains on the rare
items it evaluated. A known bug remains: the gate over-abstains on a
subset of common diagnoses (`hypertension` returning NO_CONFIDENT_MATCH).
This is not a rare-diagnosis failure — it is a gate calibration issue
documented in FINDINGS.

### 3.6 Status correctness (SOW 8.3)

**Target:** ≥ 0.90 of accepted medications and diagnoses carry the
correct status.

**Result:** _pending, from `python -m src.eval.status_eval 100`._

**Method.** For each extracted diagnosis and medication that matches a
gold item, compare the `status` field. Reports both a raw accuracy and a
confusion matrix (gold status → predicted status) so systematic biases
are visible.

### 3.7 ICD-10 coding accuracy (SOW 8.4a)

**Target:** ≥ 0.75 top-3 accuracy on gold diagnoses.

**Result:** _pending, from `python -m src.eval.icd_eval 100`._

**Method.** For each gold diagnosis with an `icd_code`, find the matching
extraction, call `icd_lookup` on its `normalised_name`, and check whether
the gold code appears in the top-1 or top-3. Reports top-1 accuracy,
top-3 accuracy, and the fraction of gold diagnoses that had no matching
extraction (counted as misses).

### 3.8 Contradiction detection (SOW 8.5)

**Target:** ≥ 0.80 of planted contradictions flagged.

**Set:** `eval_sets/contradiction.json` — 20 notes, each with a single
planted contradiction between two sections (diagnosis negation,
medication status flip, allergy negation, procedure negation).

**Result:** _pending, from `python -m src.eval.contradiction_eval`._

### 3.9 Adversarial handling (SOW 8.7)

**Target:** 100% of adversarial notes handled correctly (embedded
instructions ignored, protected information masked).

**Set:** `eval_sets/adversarial.json` — 10 notes: 5 instruction
injections, 5 fake-PII injections.

**Result:** _pending, from `python -m src.eval.adversarial_eval`._

### 3.10 Abstention quality (SOW 3.9 / 8.6)

**Target:** report flagging precision and flagging recall; show that
flagged items are genuinely harder than accepted items.

**Result:** _pending, from `python -m src.eval.abstention_eval`._

---

## 4. Failure analyses

Per SOW Section 8.9, at least three concrete cases where the system
performed poorly, with explanations.

### Failure 1 — Diagnoses F1 below the SOW target

- **Observation:** on the 57-note baseline, diagnoses P=0.686, R=0.758, F1=0.720. Target is ≥0.80. The 100-note run will confirm whether Task B/C closed the gap.
- **Root cause:** four distinct patterns, none dominant.
  1. **Extractor returns a descriptive phrase where gold has the shorter entity name.** Example from note_023: gold `"sleep apnea"` and `"Morbid obesity"`, extractor `"History of sleep apnea with reversal after 100-pound weight loss."` and `"Morbid obesity with bmi of 39.4."`.
  2. **Name variation with staging.** Example from note_026: gold `"squamous cell carcinoma of his glottic larynx"`, extractor `"T3 squamous cell carcinoma of his glottic larynx"`.
  3. **Recall misses.** Gold diagnoses not found at all: `"hallucinations"`, `"psychosis"` (note_006), `"heart attack"`, `"hiatal hernia"`, `"polyps"`, `"urinary stress incontinence"` (note_030), `"compression fractures"` (note_032).
  4. **Category errors.** Extractor emits symptoms and lab values the guideline excludes: `"allergies"` as a diagnosis, `"diminished taste"`, `"xerostomia"`, `"BMI is 38.5"`.
- **Evidence:** `docs/FINDINGS.md` entry "Failure mode taxonomy".
- **Proposed fix:** (a) matcher-side prefix and subset tolerance; (b) extractor prompt tightening (Task B, applied); (c) section-by-section extraction or second-pass extraction for recall.

### Failure 2 — Medications F1 below the SOW target

- **Observation:** on the 57-note baseline, medications P=0.697, R=0.791, F1=0.741. Target is ≥0.85.
- **Root cause:** two distinct patterns.
  1. **Intraoperative drugs extracted as patient medications.** `lidocaine`, `epinephrine`, `Marcaine`, `Xylocaine`, `Kefzol` — about 12 false positives across the baseline corpus. Addressed by Task B prompt tightening; outcome measured in the 100-note run.
  2. **Recall misses.** Gold medications not found: `Norvasc`, `Lopressor`, `lovastatin`, `citalopram`, `vitamin D`, `Risperdal`, `Levothyroxine`, `Diovan`, `albuterol`, `Advair Diskus`, `Detrol`.
- **Proposed fix:** (a) prompt tightening for intraoperative drugs (applied); (b) section-by-section extraction for medications.

### Failure 3 — Procedures precision is weak

- **Observation:** on the 57-note baseline, procedures P=0.487, R=0.704, F1=0.576. Procedures are not graded by SOW Section 8.1 but are reported.
- **Root cause:** three patterns.
  1. **Extractor over-specifies procedure names.** Example from note_008: gold `"Full-mouth extraction"`, extractor `"Full-mouth extraction of tooth #3,5,6, ... and alveoloplasty in all four quadrants"`. Addressed by Task C.
  2. **Lab tests extracted as procedures.** `CBC`, `Chem-7`, `U/A`, `CEREBROSPINAL FLUID CULTURE`, `toxicologic analysis`. Addressed by Task B.
  3. **Autopsy itself extracted as a procedure.** Addressed by Task B.
- **Proposed fix:** prompt tightening (applied); matcher-side tolerance for over-specified names.

### Failure 4 — Vitals extraction is weak

- **Observation:** on the 57-note baseline, vitals P=0.431, R=0.378, F1=0.403. Vitals are not graded by SOW Section 8.1.
- **Root cause:** two issues.
  1. **Span convention mismatch.** Gold spans the value (e.g. `"124/78"`); extractor spans the name. The matcher's span-containment fix bridges most of this.
  2. **Organ weights and non-vital measurements extracted as vitals** in autopsy and radiology reports.
- **Proposed fix:** update the labelling guideline to define a consistent span convention for vitals; prompt tightening to exclude organ weights.

### Failure 5 — Verifier disagreements across model versions

- **Observation:** the same input produced different verdicts on Gemini 3.8 Flash vs Gemini 3.5 Flash Lite.
- **Root cause:** ambiguous items (e.g. "loratadine mentioned as a possible alternative") are interpreted differently by different models.
- **Evidence:** `docs/FINDINGS.md` entry on the loratadine case.
- **Proposed fix:** more explicit category rules in the verifier prompt; second verifier pass for ambiguous items.

### Failure 6 — Duplicate note in the source dataset

- **Observation:** `note_041` is a verbatim duplicate of `note_024`.
- **Root cause:** `mtsamples.csv` lists the same note under two specialties.
- **Proposed fix:** deduplicate notes by text hash during selection.

### Failure 7 — ICD-10 confidence gate over-abstains on some common diagnoses

- **Observation:** after the token-overlap gate was introduced, a subset of common diagnoses (`hypertension`, `obesity`, `peptic ulcer disease`) returned `NO_CONFIDENT_MATCH` even though they code cleanly to common ICD-10 codes.
- **Root cause:** the gate compares the query against the top-1 vector hit's description. After re-indexing with the cleaned descriptions, the top-1 vector hit for some common queries is a related but differently-worded code whose description does not share enough tokens.
- **Impact:** this inflates the "no confident match" rate and reduces top-3 accuracy on common diagnoses.
- **Proposed fix:** evaluate token-overlap against the fused top-3 candidates, not just the vector top-1. Tracked in FINDINGS.

---

## 5. Gap analysis and improvement plan

**For diagnoses (target +0.080 from the 57-note baseline):**
1. **Matcher-side prefix/subset tolerance.** Would catch the `"T3 squamous cell carcinoma..."` vs `"squamous cell carcinoma..."` pattern and the long-descriptive-phrase pattern. Estimated +0.02 to +0.04 F1.
2. **Prompt tightening for category errors (Task B, applied).** Would remove ~10 symptom/lab-value false positives. Estimated +0.01 to +0.02.
3. **Recall improvement via section-by-section extraction.** Estimated +0.03 to +0.05.

**For medications (target +0.109 from the 57-note baseline):**
1. **Prompt tightening for intraoperative drugs (Task B, applied).** Would remove ~12 false positives. Estimated +0.03 to +0.05.
2. **Recall improvement via section-by-section extraction for the medications section.** Would recover ~28 missed items. Estimated +0.04 to +0.06.
3. **Matcher-side suffix tolerance for "X with Y" name variations.** `"Tylenol"` vs `"Tylenol with Codeine"`. Estimated +0.01 to +0.02.

**For procedures (not graded but reported):**
1. **Prompt tightening for lab tests and autopsies (Task B, applied).**
2. **Prompt tightening for over-specified procedure names (Task C, applied).**
3. **Matcher-side tolerance for over-specified procedure names.**

**Honest framing.** On the 57-note baseline, the projected diagnoses F1 after fixes was 0.78–0.82 and medications 0.80–0.85. The 100-note run will show the realized numbers. If targets are still not met, the eval report documents the gap honestly and the improvement paths clearly.

---

## 6. Cost and latency

- **Extractor:** 1 LLM call per note.
- **Verifier:** 1 LLM call per note.
- **Median latency:** _to be measured, from `python -m src.eval.cost_eval`._ The orchestrator now records `extract took X.XXs` and `verify took X.XXs` per note in the trace; the cost script parses those and reports median and p95.
- **Free-tier constraints:** Groq's ~8,000 TPM limit is the binding constraint for batch runs. Fresh 100-note runs at pace=60 take 60–120 minutes. Gemini's free tier is more permissive; 3.5 Flash Lite is stable across the batch.
- **Model calls per note:** 2 in verified mode (1 extractor + 1 verifier), 1 in raw mode.
- **Caching effect:** with a warm cache, repeated runs of the same 100 notes complete in seconds. The cache is keyed by model, both prompts, the schema/guardrails fingerprint, and the note text.

---

## 7. Limitations

1. **Gold standard is LLM-assisted across 100 notes.** Bounded by the planned hand spot-check of 15 notes. Two real inconsistencies noted: vitals span convention, and one duplicate note.
2. **Diagnoses and medications F1 targets may not be met.** Documented in Failure Analyses 1 and 2. The gap is real, not a measurement artifact.
3. **Verifier net effect on aggregate F1 is small.** Documented in Section 3.2. The verifier is doing real work at the item level (correct rejections of non-prescriptions and category errors).
4. **Vitals and procedures extraction are weak** relative to the graded entities.
5. **Free-tier rate limits constrain batch evaluation.** Full fresh runs of 100 notes take 60–120 minutes.
6. **ICD-10 confidence gate over-abstains on some common diagnoses.** Documented in Failure 7.
7. **No hand spot-check of the gold standard yet.** Planned.

---

## 8. Reproducibility

- Commit hash at time of report: _to be filled at freeze time_.
- Eval commands:
  - `python -m src.eval.run_eval 100 60` (RAW, all entities)
  - `python -m src.eval.run_eval 100 60 --verify` (VERIFIED)
  - `python -m src.eval.span_eval 100` (span faithfulness)
  - `python -m src.eval.status_eval 100` (status correctness)
  - `python -m src.eval.icd_eval 100` (ICD top-1/top-3)
  - `python -m src.eval.rare_eval` (rare-diagnosis abstention)
  - `python -m src.eval.contradiction_eval` (contradiction detection)
  - `python -m src.eval.adversarial_eval` (adversarial handling)
  - `python -m src.eval.abstention_eval` (flagging precision/recall)
  - `python -m src.eval.cost_eval 100` (latency)
- All LLM responses are cached on disk. Re-running with the same code produces identical numbers.
- Model IDs and prompt versions are frozen at the commit above.

---

## 9. Conclusion

The pipeline works end-to-end: raw clinical note → structured items with verbatim evidence and character spans → ICD-10 candidates → independent verification → reconciliation → accepted and flagged outputs. Every accepted item carries a span; the schema rejects items without one; the verifier is independent and fails closed.

The gold standard is complete at 100 notes across 26 specialties. All spans are verified programmatically (`src/utils/verify_gold.py`). The evaluation harness covers every metric SOW Section 3.9 requires: entity-level F1 for five entity types, RAW vs VERIFIED comparison, span faithfulness, ICD-10 top-1 and top-3, status correctness, rare-diagnosis abstention, contradiction detection, adversarial handling, abstention quality, and cost and latency.

Accuracy targets for diagnoses (≥0.80) and medications (≥0.85) are the primary open question. The 57-note baseline showed both below target. Task B and Task C prompt changes have been applied since; the 100-note run will show the realized numbers, and the improvement paths are documented concretely in Section 5.

The system's central claim — **every accepted item is provable** — is enforced by design: mandatory spans, verifier independence, and fail-closed behavior at every stage. No item is accepted without evidence. This is the property the SOW emphasizes above raw F1, and it holds.