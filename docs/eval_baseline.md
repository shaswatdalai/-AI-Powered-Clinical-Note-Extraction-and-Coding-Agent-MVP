# Evaluation Baseline

**Author:** Shaswat Kumar Dalai
**Purpose:** Consolidated record of evaluation metrics across development stages. Updated as gold notes are added, prompts are tuned, and the verifier is integrated.

---

## Setup

- **Extractor model:** Qwen 3.8 27B (via Groq, free tier, temperature 0)
- **Verifier model:** Gemini 3.5 Flash Lite (via Google AI Studio, free tier, temperature 0)
- **Matching rules:** exact match only (normalised name equality AND span IoU ≥ 0.5)
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
- Vitals: F1 = 0.16 — the biggest weakness. Both under- and over-extraction.
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
- Procedures and vitals unchanged — verifier category check does not currently apply to those entity types.
- **Net effect: verifier improves precision without hurting recall.** Working as designed.

---

## Baseline 4 — 42 notes, verified (in progress)

Full 42-note run with verifier applied. Metrics will populate once the run completes.

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | _pending_ | _pending_ | _pending_ | | | |
| Medications | _pending_ | _pending_ | _pending_ | | | |
| Procedures | _pending_ | _pending_ | _pending_ | | | |
| Allergies | _pending_ | _pending_ | _pending_ | | | |
| Vitals | _pending_ | _pending_ | _pending_ | | | |

**Expected direction of change vs Baseline 2:**
- Diagnoses: precision rises, recall roughly unchanged.
- Medications: precision rises.
- Procedures and vitals: minimal change until verifier category check is extended.

---

## Gap analysis against SOW targets

| Entity | Current F1 (Baseline 2, 42 notes) | SOW target | Gap |
|---|---|---|---|
| Diagnoses | 0.720 | 0.80 | 0.08 short |
| Medications | 0.589 | 0.85 | 0.26 short |
| Procedures | 0.531 | — (no explicit target) | — |
| Vitals | 0.156 | — (no explicit target) | — |

**Diagnoses** are close to target. Verifier integration should close the gap.
**Medications** need more work — likely both prompt tightening and verifier category coverage.

---

## Improvement plan (ordered by expected impact)

1. **Apply verifier to the full 42 notes** — filter REJECTED items before computing metrics. Expected gain on precision.
2. **Extend verifier category check to procedures and vitals** — reject exam components, imaging descriptions, and non-vital measurements.
3. **Tighten extractor's vitals section** — vitals are both over- and under-produced. Explicit rules on which values count as vitals.
4. **Tighten extractor's procedures definition** — exclude routine exam components and descriptions of findings.
5. **Add lenient match reporting** — report both strict and partial-match F1 to distinguish near-misses from total errors.
6. **Remove ICD description wrapper text** — cleaner descriptions improve retrieval quality.

---

## Determinism and reproducibility

Every LLM call (extractor and verifier) is cached on disk keyed by `hash(model + prompt + input)`. Given:

- The same gold notes
- The same extractor and verifier prompts
- The same model IDs
- The same random seeds and temperature (0)

...the eval produces identical metrics on every run. This satisfies SOW Section 4.2 (reproducibility) and Section 3.9 (evaluation harness) requirements.

**Cache invalidation:** changing any of the following invalidates the cache and forces fresh LLM calls:

- Extractor model ID
- Extractor system or user prompt
- Verifier model ID
- Verifier system or user prompt
- Note text (if masked differently)

Changing the schema, matching rules, or evaluation script does **not** invalidate LLM cache — those layers sit above the cached responses.

---

## Change log

- **v1 (8 Oct 2026):** Initial baseline on 5 notes (Baseline 1).
- **v2 (9 Oct 2026):** Extended to 42 notes (Baseline 2). Verifier integration complete; 5-note verified baseline recorded (Baseline 3).
- **v3 (9 Oct 2026):** Consolidated all baselines into one document with consistent structure and gap analysis.