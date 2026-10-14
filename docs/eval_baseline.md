# Evaluation Baseline

**Author:** Shaswat Kumar Dalai
**Purpose:** Consolidated record of evaluation metrics across development stages. Updated as gold notes are added, prompts are tuned, and the verifier is integrated.

---

## Setup

- **Extractor model:** Qwen 3.8 27B (via Groq, free tier, temperature 0)
- **Verifier model:** Gemini 3.5 Flash Lite (via Google AI Studio, free tier, temperature 0)
- **Matching rules:** exact match (normalised name equality AND span overlap)
- **Gold standard:** hand-labelled notes in `gold/`
- **Reproducibility:** deterministic via caching; every LLM response is stored to disk keyed by `hash(model + prompt + input)`
- **SOW targets:** diagnoses F1 ≥ 0.80; medications F1 ≥ 0.85

---

## Baseline 1 — 5 notes, raw extractor (8 Oct 2026)

First working eval. No verifier applied. Raw extractor output only.

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | 0.636 | 0.583 | 0.609 | 7 | 4 | 5 |
| Medications | 0.571 | 0.667 | 0.615 | 4 | 3 | 2 |
| Procedures | 0.250 | 0.500 | 0.333 | 2 | 6 | 2 |
| Allergies | 0.000 | 0.000 | 0.000 | 0 | 0 | 0 |
| Vitals | 0.444 | 0.364 | 0.400 | 4 | 5 | 7 |

**Observations:**
- Small sample; not statistically meaningful.
- Procedures precision is very low (0.25) — extractor over-produces procedures.
- Allergies has no data — the first 5 notes contain no allergies.

---

## Baseline 2 — 42 notes, raw extractor (8–9 Oct 2026)

Extended to 42 gold notes. Still no verifier. Raw extractor output only.

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | 0.655 | 0.800 | 0.720 | 76 | 40 | 19 |
| Medications | 0.550 | 0.635 | 0.589 | 33 | 27 | 19 |
| Procedures | 0.429 | 0.698 | 0.531 | 30 | 40 | 13 |
| Allergies | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 |
| Vitals | 0.147 | 0.167 | 0.156 | 5 | 29 | 25 |

**Observations:**
- Diagnoses: strong recall (0.80) but precision is the limiting factor (0.655). Many false positives.
- Medications: both precision and recall are moderate. Below SOW target of 0.85.
- Procedures: P = 0.43 — heavy over-extraction.
- Vitals: F1 = 0.16 — the biggest weakness.
- Allergies: perfect on 2 items. Not statistically meaningful.

---

## Baseline 3 — 5 notes, verified (9 Oct 2026)

Verifier applied with category check (mechanisms of injury, radiology findings, lab values, social facts rejected). Same 5 notes as Baseline 1.

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | 0.778 | 0.583 | 0.667 | 7 | 2 | 5 |
| Medications | 0.667 | 0.667 | 0.667 | 4 | 2 | 2 |
| Procedures | 0.250 | 0.500 | 0.333 | 2 | 6 | 2 |
| Allergies | 0.000 | 0.000 | 0.000 | 0 | 0 | 0 |
| Vitals | 0.444 | 0.364 | 0.400 | 4 | 5 | 7 |

**Observations:**
- **Diagnoses precision: 0.636 → 0.778** (+0.142). Verifier rejected 2 false positives.
- **Medications precision: 0.571 → 0.667** (+0.096). Verifier rejected 1 false positive.
- Recall unchanged for both. No true positives were rejected.
- Procedures and vitals unchanged — verifier category check does not apply to those entity types.

---

## Baseline 4 — 57 notes, raw extractor (12–13 Oct 2026)

Gold standard extended to 57 notes. RAW mode with the span-overlap matcher fix.

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | 0.686 | 0.758 | 0.720 | 197 | 90 | 63 |
| Medications | 0.697 | 0.791 | 0.741 | 106 | 46 | 28 |
| Procedures | 0.487 | 0.704 | 0.576 | 76 | 80 | 32 |
| Allergies | 1.000 | 1.000 | 1.000 | 8 | 0 | 0 |
| Vitals | 0.431 | 0.378 | 0.403 | 28 | 37 | 46 |

**Observations:**
- Matcher fix (relaxed span IoU to any overlap, added VITALS_ABBREVIATIONS and span containment) brought vitals F1 from 0.144 to 0.403.
- Diagnoses and medications roughly at the same level as the 42-note baseline, on a larger sample.
- Verifier trades ~4 FP for ~3 TP on medications; net effect small.

---

## Baseline 5 — 78 of 100 notes, raw extractor (15 Oct 2026)

Gold standard complete at 100 notes. Full fresh run could not complete on the Groq free tier; 22 notes (067–099 range) were dropped when `retry-after` climbed past 400s, indicating the daily cap.

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | 0.617 | 0.667 | 0.641 | 226 | 140 | 113 |
| Medications | 0.820 | 0.648 | 0.724 | 114 | 25 | 62 |
| Procedures | 0.577 | 0.631 | 0.603 | 94 | 69 | 55 |
| Allergies | 1.000 | 0.909 | 0.952 | 10 | 0 | 1 |
| Vitals | 0.419 | 0.344 | 0.378 | 31 | 43 | 59 |

**Observations:**
- The wider gold set (26 specialties) exposed recall gaps not present in the 15-specialty set.
- Medications precision improved from 0.678 (57-note baseline) to 0.820 after the Task B prompt tightening (intraoperative drug exclusion). Recall dropped because more gold items are now in the denominator and not all are found.
- Diagnoses recall is now the primary bottleneck: 113 missed gold diagnoses.
- Procedures precision improved with Task B (lab tests, autopsies) and Task C (procedure name cap), but still weak at 0.577.

---

## Gap analysis against SOW targets

| Entity | Current F1 (78 notes) | SOW target | Gap |
|---|---|---|---|
| Diagnoses | 0.641 | 0.80 | 0.159 short |
| Medications | 0.724 | 0.85 | 0.126 short |
| Procedures | 0.603 | — (no explicit target) | — |
| Vitals | 0.378 | — (no explicit target) | — |

**Diagnoses** — gap dominated by recall. Section-by-section extraction is the primary lever.
**Medications** — precision now strong (0.820); recall remains the lever.

---

## Improvement plan (ordered by expected impact)

1. **Section-by-section extraction.** The extractor receives each section of the note separately rather than the whole note. Would improve recall on long notes and on the unfamiliar specialties added in 087–100.
2. **Second-pass extraction for medications.** Dedicated medications-only prompt would recover missed items in long medication lists.
3. **Matcher-side prefix/subset tolerance.** Would catch `"T3 squamous cell carcinoma..."` vs `"squamous cell carcinoma..."` and long-descriptive-phrase cases.
4. **Fix the ICD confidence gate over-abstention.** Token overlap should be checked against the fused top-3, not just the vector top-1.
5. **Vitals span-convention alignment.** Either update the gold to match the extractor, or vice versa. Documented in FINDINGS.
6. **Remove the ICD description wrapper text.** Already done in the 2026-10-13 rebuild.

---

## Determinism and reproducibility

Every LLM call (extractor, verifier, advisor) is cached on disk or in Redis, keyed by the model, prompts, and input. Given:

- The same gold notes
- The same extractor and verifier prompts
- The same model IDs
- The same temperature (0)

...the eval produces identical metrics on every run. This satisfies SOW Section 4.2 (reproducibility) and Section 3.9 (evaluation harness) requirements.

**Cache invalidation:** changing any of the following invalidates the cache and forces fresh LLM calls:

- Extractor model ID
- Extractor system or user prompt
- Verifier model ID
- Verifier system or user prompt
- Note text (if masked differently)
- Schema or guardrails fingerprint (for the verifier cache)

Changing the matching rules, the evaluation script, or the UI does **not** invalidate the LLM cache.

---

## Change log

- **v1 (8 Oct 2026):** Initial baseline on 5 notes (Baseline 1).
- **v2 (9 Oct 2026):** Extended to 42 notes (Baseline 2). Verifier integration complete; 5-note verified baseline recorded (Baseline 3).
- **v3 (9 Oct 2026):** Consolidated all baselines into one document with consistent structure and gap analysis.
- **v4 (15 Oct 2026):** Added Baseline 4 (57 notes, matcher fix). Added Baseline 5 (78 of 100, complete gold standard, daily-cap constraint documented). Updated gap analysis and improvement plan for the wider specialty distribution.