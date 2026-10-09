# Findings Log

Running log of issues, divergences, and notable behaviors encountered during development. Updated as we build and test. Feeds directly into the final evaluation report's failure analyses.

Format per entry:
- **Date** — when observed
- **Severity** — critical / high / medium / low / note
- **Where** — component or file
- **What** — observation
- **Action** — fixed / deferred / accepted
- **Notes** — anything else

---

## 2026-10-07 — Day 1 (initial build)

### Extractor — note_001 divergences

- **Severity:** note (informational)
- **Where:** `src/extractor.py` running on `data/note_001.txt`
- **What:** Extractor returned 2 diagnoses, 5 medications, 2 vitals. Gold expects 3 diagnoses, 4 medications, 2 vitals.
  - Missing: "allergies" as a diagnosis. LLM treated it as a chief complaint, not a formal diagnosis.
  - Extra: 5 medications returned vs 4 in gold.
  - Correct: asthma `[520, 526]`, Allergic rhinitis `[1028, 1045]` — exact span match with gold.
- **Action:** Deferred. Assess across all gold notes before deciding whether to adjust the extractor prompt.
- **Notes:** This is the kind of divergence the evaluation measures. A judgment call, not necessarily a bug.

### Masker — over-masking of "Allergic"

- **Severity:** high (fixed 2026-10-07)
- **Where:** `src/masker.py`
- **What:** spaCy labelled "Allergic" (single token) as a PERSON entity. The masker replaced it with `XXXXXXXXX`, breaking extraction for "Allergic rhinitis".
- **Action:** Fixed. Added a `CLINICAL_BLOCKLIST` of clinical terms, and a rule to skip single-token entities.
- **Notes:** Trade-off: names like "Cher" (single word) wouldn't be masked. Acceptable for clinical notes where names are usually multi-token.

### Extractor — span covered evidence quote, not name

- **Severity:** high (fixed 2026-10-07)
- **Where:** `src/extractor.py`, function `_build_extraction`
- **What:** The span resolver targeted the LLM's `evidence_quote`, which the LLM often returns as a full sentence. Produced spans much longer than the gold standard. Example: asthma span was `[506, 611]` (105 chars) instead of `[520, 526]` (6 chars).
- **Action:** Fixed. Span resolver now prefers the entity's canonical name, falling back to the evidence quote only when the name cannot be located.
- **Notes:** Design decision made explicit: the span represents the entity text, not the evidence context.

### Groq API — 401 Unauthorized

- **Severity:** high (fixed 2026-10-07)
- **Where:** `src/extractor.py`, initial run
- **What:** First API call to Groq returned 401 Unauthorized.
- **Action:** Fixed. Wrote `src/utils/check_groq.py` to isolate the issue. The key was valid; the model ID was missing the `qwen/` provider prefix. Corrected `GROQ_MODEL` from `qwen-3.8-27b` to `qwen/qwen3.8-27b`.
- **Notes:** Groq model IDs include a provider prefix. Common gotcha when switching between providers. Future integrations should list `/models` first.

### ChromaDB batch size limit

- **Severity:** high (fixed 2026-10-07)
- **Where:** `src/icd_index.py`, `build_index()`
- **What:** `collection.add()` with all 74,260 items at once failed with `ValueError: Batch size of 74260 is greater than max batch size of 5461`.
- **Action:** Fixed by chunking into batches of 5,000.
- **Notes:** Known limitation of the Rust-backed Chroma bindings. Not prominently documented in the Python docs.

### ICD-10 description field contains wrapper text

- **Severity:** medium (deferred)
- **Where:** `src/icd_index.py`, descriptions loaded from `data/icd10cm_data.csv`
- **What:** The `description` column contains wrapper text: `Header: <parent> | Specific long description about this code: <actual>`. This pollutes BM25 tokens and embedding representation.
- **Action:** Deferred. Impact is minor — the correct code still ranks highly. To fix: strip the wrapper before indexing.
- **Notes:** Observed during build. Would matter more if the description text were shown directly to the user without cleanup. The verifier sees this text, so a cleaner version would improve judgment quality.

### End-to-end pipeline works on note_001

- **Severity:** note (success)
- **Where:** `src/utils/try_pipeline.py`, running on `data/note_001.txt`
- **What:** The pipeline ran cleanly: note → mask (2 items, same length) → extract (2 dx, 5 meds, 2 vitals) → ICD lookup.
- **Correct ICD chapter matches:**
  - asthma → J45.998, J45.902, J45.991
  - Allergic rhinitis → J30.89, J30.81, J30.9
- **Action:** None. Milestone.
- **Notes:** Diagnoses converged on correct ICD-10 chapters on first integration test.

### Autopsy notes over-extracted as diagnoses

- **Severity:** high (fixed 2026-10-07)
- **Where:** `src/extractor.py` running on `data/note_002.txt` (autopsy)
- **What:** Extractor returned 24 diagnoses for an autopsy note whose gold standard has 3. It treated every forensic finding (petechial hemorrhaging, injuries, lesions, pregnancy status, etc.) as a diagnosis.
- **Action:** Fixed. Added an explicit "DO NOT extract" list and an autopsy special case to the system prompt.
- **Notes:** Verified after the fix: note_002 extracts 3 diagnoses (exact match with gold), note_005 extracts 2 (exact match).

### Groq 429 rate limits

- **Severity:** medium (mitigated 2026-10-07)
- **Where:** `src/extractor.py`, `src/utils/eval_batch.py`
- **What:** Processing 12+ notes back-to-back hit Groq's TPM limit. The extractor crashed on note_003.
- **Action:** Mitigated. Added explicit 429 handling in `_call_groq()` that reads the `Retry-After` header and sleeps before retrying. Added pacing to `eval_batch.py`. Reduced prompt size, which also reduced per-call token usage.
- **Notes:** Free-tier Groq has ~30 RPM and ~8K TPM for Qwen. Each note uses ~1,000 tokens, so effective throughput is ~7 notes per minute. This is a SOW-acknowledged constraint (Section 7.2).

### Note_016 (Carotid Duplex Report) — kept empty

- **Severity:** low (accepted)
- **Where:** `gold/note_016.json`
- **What:** Note_016 is a vascular ultrasound report. Findings are imaging observations ("heterogeneous plaque", "stenosis ~70%", peak systolic velocities). Initially considered extracting the plaque findings as diagnoses; decided to leave the arrays empty.
- **Action:** Accepted. Consistency with the autopsy rule — imaging observations are findings, not diagnoses. Empty gold is a legitimate label for a report that describes only findings.
- **Notes:** Two defensible positions exist. Documented so the choice is explicit in the evaluation report.

---

## 2026-10-09 — Day 3 (verifier + eval)

### Verifier correctly rejects over-extracted medication (note_001)

- **Severity:** note (success)
- **Where:** `src/verifier.py` running on note_001
- **What:** Extractor returned 5 medications including "loratadine" (mentioned in the note only as a possible alternative: *"Another option will be to use loratadine"*). The verifier rejected it as "not prescribed or initiated." This is the fail-closed behavior the SOW requires.
- **Action:** None. Logged as evidence the verifier is doing real work.
- **Notes:** Concrete example of extractor-verifier independence providing value. Material for the evaluation report's discussion of precision vs recall trade-offs.

### Verifier missed vitals on note_001 (recall check working)

- **Severity:** note (success)
- **Where:** `src/verifier.py` running on note_001
- **What:** Verifier's recall check flagged two vitals the extractor missed:
  - Weight 130 pounds
  - Blood pressure 124/78
  Both are in the note but the extractor did not produce them.
- **Action:** Accepted. The verifier correctly identified the gap.
- **Notes:** Also flagged "no known medicine allergies" as missed, which is a false positive (a negation is not an allergy). Verifier isn't perfect; documented.

### Extractor fails on note_020 due to invalid medication status

- **Severity:** high (fixed 2026-10-09)
- **Where:** `src/extractor.py`
- **What:** The extractor LLM returned a medication whose `status` value wasn't one of the three enum values. Pydantic rejected the whole response, so the note was skipped.
- **Action:** Fixed by (1) adding a status normalization map that maps LLM synonyms ("taking", "active", "past") to valid enums, and (2) wrapping each item's Pydantic construction in try/except so a single bad item is dropped without killing the note.
- **Verified:** Note_020 now processes cleanly — 6 diagnoses and 3 medications extracted. Full eval on 42 notes completes with 0 skips.
- **Notes:** This class of error (LLM returns a value near the enum but not exactly) is common on the free-tier Qwen model. Robustness here matters for the full 100-note eval.

### ICD confidence threshold is 0.55, calibrated on test queries

- **Severity:** note (design decision)
- **Where:** `src/icd_index.py`, `MIN_COSINE_CONFIDENCE = 0.55`
- **What:** The SOW requires a "no confident match" path but doesn't specify the threshold. Chose 0.55 based on test queries: common diagnoses (asthma, type 2 diabetes, allergic rhinitis) return top cosine 0.87–0.91; rare or ambiguous queries fall below 0.55.
- **Action:** Documented in `ARCHITECTURE.md` Section 8. Threshold can be refined against the rare-diagnosis test set when that's built.
- **Notes:** `CONFIDENCE_THRESHOLD=0.70` in `.env` is a separate value (not currently used). Consider consolidating or removing.

### Verifier model stability — switched to Gemini 3.5 Flash Lite

- **Severity:** high (fixed 2026-10-09)
- **Where:** `src/verifier.py`
- **What:** Gemini 3.8 Flash returned HTTP 503 ("model experiencing high demand") on nearly every call. Google's infrastructure for that specific model was overloaded. Retries with exponential backoff didn't recover within the retry budget.
- **Action:** Switched verifier to **Gemini 3.5 Flash Lite** — same Google family (independence from Qwen extractor maintained), lower traffic tier, markedly more stable. Verifier now runs reliably with no retries required.
- **Notes:** Model availability on the free tier varies by demand. The SOW requires a Google Gemini Flash variant for independence; 3.5 Flash Lite satisfies this while being stable enough for batch processing.

### Verifier disagreements across Gemini versions

- **Severity:** note (documented)
- **Where:** `src/verifier.py`, verdicts on note_001
- **What:** The same input produced different verdicts across Gemini model versions:
  - Gemini 3.8 Flash: `m4 (loratadine)` → REJECTED (mentioned as option, not prescribed)
  - Gemini 3.5 Flash Lite: `m4 (loratadine)` → SUPPORTED (mentioned in plan)
  Both positions are defensible — the note says "another option will be to use loratadine," ambiguous between consideration and prescription.
- **Action:** Accepted. Documented as evidence that verifier verdicts are model-dependent on ambiguous items.
- **Notes:** This is why caching verifier outputs matters. Changing the verifier model invalidates the cache and produces different metrics — the eval must be run with one model consistently.

### Verifier category-check improvement

- **Severity:** high (improvement 2026-10-09)
- **Where:** `src/prompts/verifier_system.txt`
- **What:** Initial verifier prompt only asked "is this item supported by the note?" The extractor's dominant error mode was category confusion (mechanisms of injury, radiology findings, lab values labelled as diagnoses). The permissive prompt let these pass through.
- **Action:** Tightened the verifier prompt to explicitly reject incorrect categories:
  - mechanism of injury
  - physical exam finding
  - radiology finding
  - lab value or measurement
  - social fact
  - family history
  - normal state
- **Result on 5 notes:**
  - Diagnoses precision: 0.636 → 0.778 (+0.142)
  - Medications precision: 0.571 → 0.667 (+0.096)
  - Recall unchanged
- **Notes:** Procedures and vitals unchanged. Could be addressed with category checks for those entity types too. Deferred.

### Note_041 is a duplicate of note_024

- **Severity:** low (accepted)
- **Where:** `data/note_041.txt`, source `mtsamples.csv`
- **What:** Note_041 is verbatim identical to note_024. Both are a tracheostomy/thyroid isthmusectomy procedure. The MTSamples dataset lists this content under two specialties (ENT and Endocrinology).
- **Action:** Accepted. Gold labels for note_041 are consistent with note_024's labels, with updated specialty and source index.
- **Notes:** Duplication in the source dataset. Will slightly overweight this content in evaluation metrics. Worth mentioning in the evaluation report. A future improvement: deduplicate notes by text hash during selection.

---

## Open items (not yet fixed or decided)

- **Vitals extraction is weak** (F1 ≈ 0.16 on 42 notes). Vitals are both over- and under-extracted. Prompt tightening is deferred.
- **Procedures precision is weak** (P = 0.43 on 42 notes). Extractor over-produces procedures; verifier category check doesn't currently address procedures specifically.
- **ICD description wrapper text** is still in the index. Deferred.
- **Extractor produces wrong-category items as diagnoses** despite the prompt's "DO NOT extract" list. The verifier catches most but not all. Ongoing tuning.