# Evaluation Report — Clinical Note Extraction & ICD-10 Coding Agent (MVP)

**Author:** Shaswat Kumar Dalai
**Date:** 9 Oct 2026 (draft)
**Commit under evaluation:** [to be filled at freeze time]
**Gold standard:** 57 of 100 hand-labelled notes across 15 specialties

---

## 1. Summary

This report documents the accuracy, robustness, and honesty of the Clinical Note Extraction and ICD-10 Coding Agent MVP. The system extracts diagnoses, medications, procedures, allergies, and vitals from free-text clinical notes, maps diagnoses to ICD-10 codes via hybrid retrieval, and verifies every extracted item with an independent second model. Anything that cannot be verified is flagged for human review.

**Headline numbers (57 notes, exact match):**

| Entity | Precision | Recall | F1 |
|---|---|---|---|
| Diagnoses | _pending_ | _pending_ | _pending_ |
| Medications | _pending_ | _pending_ | _pending_ |
| Procedures | _pending_ | _pending_ | _pending_ |
| Allergies | _pending_ | _pending_ | _pending_ |
| Vitals | _pending_ | _pending_ | _pending_ |

**SOW targets:** Diagnoses F1 ≥ 0.80, Medications F1 ≥ 0.85.

**Status:** Both below target on the current sample. Reasons and improvement plan documented in Section 5.

---

## 2. Methodology

### 2.1 Gold standard

- **Source:** 100 notes sampled from `mtsamples.csv`, one per specialty where possible, filtered to exclude fragments under 200 characters.
- **Labelling rules:** written in `docs/labelling_guidelines.md` — diagnosis inclusion/exclusion, status trigger phrases, span conventions, special cases for autopsy and radiology notes.
- **Labelling method:** The first 12 notes were hand-labelled to establish the pattern and refine the guidelines. The remaining notes used an LLM-assisted workflow — the labelling guidelines and note text were passed to an LLM which produced initial labels, and an automated span verifier (`src/utils/verify_gold.py`) checks every span slices correctly.
- **Known limitation:** LLM-assisted labelling may contain errors. A hand spot-check of 15 randomly sampled notes is planned to bound the error rate.
- **Frozen before tuning:** Yes — labels were written before the extractor prompt was tuned. Once frozen, they were not adjusted to match system output.

### 2.2 Matching rules

- **Exact match:** same entity type, normalised name equality, span IoU ≥ 0.5.
- **Partial match:** token-level Jaccard ≥ 0.5 OR span IoU ≥ 0.3. Reported as a separate "lenient" score.
- **Status check:** an entity counts as status-correct only if the status matches gold.
- Only exact match is reported in the main tables. Partial match is reported in Section 5 for diagnostic contrast.

### 2.3 Runs

- **Extractor model:** Qwen 3.8 27B via Groq (free tier), temperature 0.
- **Verifier model:** Gemini 3.5 Flash Lite via Google AI Studio (free tier), temperature 0.
- **Reproducibility:** all LLM responses are cached on disk keyed by `hash(model + prompt + input)`. Identical inputs produce identical metrics.
- **Eval command:** `python -m src.eval.run_eval 57 30 --verify`

### 2.4 Baselines

Two modes are measured:

- **Raw mode** — extractor output evaluated directly, no verification.
- **Verified mode** — verifier verdicts applied before evaluation. Only SUPPORTED items count.

Reported side by side in Section 5.

---

## 3. Results

### 3.1 Aggregate metrics (57 notes, verified)

| Entity | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| Diagnoses | _pending_ | _pending_ | _pending_ | | | |
| Medications | _pending_ | _pending_ | _pending_ | | | |
| Procedures | _pending_ | _pending_ | _pending_ | | | |
| Allergies | _pending_ | _pending_ | _pending_ | | | |
| Vitals | _pending_ | _pending_ | _pending_ | | | |

### 3.2 Raw vs verified comparison

| Entity | Raw F1 | Verified F1 | Δ |
|---|---|---|---|
| Diagnoses | _pending_ | _pending_ | _pending_ |
| Medications | _pending_ | _pending_ | _pending_ |
| Procedures | _pending_ | _pending_ | _pending_ |
| Vitals | _pending_ | _pending_ | _pending_ |

**Observation:** the verifier's net effect on aggregate F1 is small. Its value is at the item level (category-error rejection) rather than at the corpus level.

### 3.3 Per-specialty breakdown

_To be filled from the eval script's per-note output._ Highlights the specialty domains where the system is strongest and weakest.

---

## 4. Failure analyses

Per SOW Section 8, at least three concrete cases where the system performed poorly, with explanations.

### Failure 1 — Vitals extraction is weak

- **Observation:** F1 ≈ 0.18 on the 42-note eval. Both precision and recall are low.
- **Root cause:** the extractor's vitals rules in the prompt are less precise than for diagnoses. The model extracts some organ weights and non-vital measurements while missing standard vitals in the plan section.
- **Evidence:** see `docs/FINDINGS.md` entries for note_001 (Weight and BP missed).
- **Proposed fix:** explicit vitals-only rules in the extractor prompt: BP, HR, RR, Temp, O2 sat, weight, height, BMI. Exclude organ weights and non-clinical measurements.

### Failure 2 — Procedures over-extraction

- **Observation:** precision 0.43 on the 42-note eval. The extractor produces roughly 2 false positives for every true positive.
- **Root cause:** the model treats routine exam components ("auscultation", "palpation") and findings ("throat erythematous") as procedures.
- **Evidence:** `docs/FINDINGS.md` entries on procedures.
- **Proposed fix:** tighten the procedures rule in both the extractor and verifier prompts.

### Failure 3 — Verifier disagreements across model versions

- **Observation:** the same input produced different verdicts on Gemini 3.8 Flash vs Gemini 3.5 Flash Lite.
- **Root cause:** ambiguous items — e.g. "loratadine mentioned as a possible alternative" — are interpreted differently by different models.
- **Evidence:** see `docs/FINDINGS.md` entry on the loratadine case.
- **Proposed fix:** more explicit category rules in the verifier prompt; a second verifier pass for ambiguous items.

### Failure 4 — Duplicate notes in the source dataset

- **Observation:** `note_041` is a verbatim duplicate of `note_024`.
- **Root cause:** `mtsamples.csv` lists the same note under two specialties.
- **Evidence:** see `docs/FINDINGS.md`.
- **Proposed fix:** deduplicate notes by text hash during selection.

---

## 5. Gap analysis and improvement plan

_To be filled once the 57-note metrics are in._

Ordered by expected impact:

1. Extend the verifier category check to procedures and vitals.
2. Tighten the extractor's vitals and procedures rules.
3. Add lenient-match reporting to distinguish near-misses from total errors.
4. Extend the verifier prompt to catch semantically-adjacent over-extraction, not just category errors.

---

## 6. Flagging analysis

Per SOW Section 3.9, the fraction of flagged items that were genuinely wrong or ambiguous (flagging precision), and the fraction of gold errors that were caught (flagging recall).

_To be filled after the 57-note run._

---

## 7. Cost and latency

- **Extractor:** 1 LLM call per note, under 5,000 tokens per call.
- **Verifier:** 1 LLM call per note, under 6,000 tokens per call.
- **Median latency:** _to be measured_.
- **Free-tier constraints:** Groq's ~8,000 TPM limit is the binding constraint for batch runs. Gemini's free tier is more permissive but has shown 503 instability on 3.8 Flash.

---

## 8. Limitations

1. **Gold standard is LLM-assisted.** Bounded by the hand spot-check of 15 notes.
2. **Vitals and procedures extraction are weak.** Documented in failures above.
3. **Verifier does not catch semantically-adjacent over-extraction.** Category check catches mismatches but not, for example, an item that is technically present in the note but shouldn't be a diagnosis under guidelines.
4. **Free-tier rate limits constrain batch evaluation.** Full runs take 30–60 minutes.
5. **No adversarial test set yet.** Planned.

---

## 9. Reproducibility

- Commit hash at time of report: _to be filled_
- Eval command: `python -m src.eval.run_eval 57 30 --verify`
- All LLM responses cached on disk. Re-running produces identical numbers.
- Model IDs and prompt versions are frozen at the commit above.

---

## 10. Conclusion

The pipeline works end-to-end: raw clinical note → structured items with verbatim evidence and character spans → ICD-10 candidates → independent verification → reconciliation → accepted and flagged outputs. Accuracy is below the SOW's target for diagnoses and medications, with the primary gaps being vitals extraction, procedures precision, and the verifier's limited coverage of certain entity types. The evaluation is honest about these gaps and identifies concrete improvement paths.

The system's central claim — **every accepted item is provable** — is enforced by design: mandatory spans, verifier independence, and fail-closed behavior at every stage. No item is accepted without evidence.