# Evaluation Baseline

Date: Fri 9 Oct 2026
Gold notes evaluated: 5 of 27 (first batch)
Model: Qwen 3.8 27B via Groq
Verifier: not applied (extractor output evaluated directly)
Matching: exact match only (name match + span IoU >= 0.5)

## Aggregate metrics

| Entity type | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses   | 0.636 | 0.583 | 0.609 | 7 | 4 | 5 |
| Medications | 0.571 | 0.667 | 0.615 | 4 | 3 | 2 |
| Procedures  | 0.250 | 0.500 | 0.333 | 2 | 6 | 2 |
| Allergies   | 0.000 | 0.000 | 0.000 | 0 | 0 | 0 |
| Vitals      | 0.444 | 0.364 | 0.400 | 4 | 5 | 7 |

## SOW targets

- Diagnoses F1 target: >= 0.80
- Medications F1 target: >= 0.85

## Gap analysis

- Diagnoses: 0.19 below target
- Medications: 0.24 below target
- Procedures: weak (P=0.25) — likely over-extracting exam components
- Vitals: weak recall (0.36) — extractor misses many vitals
- Allergies: no data in first 5 notes

## Hypotheses for improvement

1. Tighten vitals extraction in the extractor prompt
2. Tighten procedures definition — exclude imaging/exam components
3. Apply verifier output before evaluation (filter REJECTED items)
4. Add lenient match reporting alongside strict


# Evaluation Baseline

Date: Fri 9 Oct 2026
Gold notes evaluated: 27 (full first batch)
Model: Qwen 3.8 27B via Groq
Verifier: not applied (extractor output evaluated directly)
Matching: exact match only (name match + span IoU >= 0.5)

## Aggregate metrics

| Entity type | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses   | ... | ... | ... | ... | ... | ... |
| Medications | ... | ... | ... | ... | ... | ... |
| Procedures  | ... | ... | ... | ... | ... | ... |
| Allergies   | ... | ... | ... | ... | ... | ... |
| Vitals      | ... | ... | ... | ... | ... | ... |

## SOW targets

- Diagnoses F1 target: >= 0.80
- Medications F1 target: >= 0.85

## Observed gaps

- Diagnoses: X.XX below target
- Medications: X.XX below target
- Procedures: P=0.4X — over-extracts
- Vitals: F1=0.1X — both over- and under-extracts
- Allergies: F1=1.00 on 2 items — too few to be meaningful

## Improvement plan

1. Integrate verifier into the eval path — filter REJECTED items
   before computing metrics. Expected gain on precision.
2. Tighten vitals section in the extractor prompt.
3. Tighten procedures definition (exclude exam components).
4. Add lenient match reporting alongside strict.

# Evaluation Baseline

Date: 9 Oct 2026
Notes evaluated: 42
Extractor model: Qwen 3.8 27B (via Groq)
Verifier: not applied
Matching: exact match only

## Metrics

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses   | 0.655 | 0.800 | 0.720 | 76 | 40 | 19 |
| Medications | 0.550 | 0.635 | 0.589 | 33 | 27 | 19 |
| Procedures  | 0.429 | 0.698 | 0.531 | 30 | 40 | 13 |
| Allergies   | 1.000 | 1.000 | 1.000 | 2 | 0 | 0 |
| Vitals      | 0.147 | 0.167 | 0.156 | 5 | 29 | 25 |

## SOW targets

- Diagnoses F1 >= 0.80
- Medications F1 >= 0.85

## Gap analysis

- Diagnoses: 0.08 below target
- Medications: 0.26 below target
- Vitals: dramatically below target (F1 0.16)
- Procedures: moderate (0.53)

## Improvement hypotheses

1. Apply verifier before evaluation (filter FPs)
2. Tighten vitals in extractor prompt
3. Tighten procedures definition
4. Consider lenient matching (partial credit)