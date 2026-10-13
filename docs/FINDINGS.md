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

### Orchestrator runs end-to-end on note_001

- **Severity:** note (success)
- **Where:** `src/orchestrator.py` running on `data/note_001.txt`
- **What:** The orchestrator ties together section, mask, extract, ICD
  lookup, verify, and reconcile into one function. On note_001:
  - 8 sections detected
  - 2 PII items masked, length preserved
  - 9 items extracted
  - Verifier accepted 8, rejected 1 (loratadine — "only mentioned as
    another option to consider, not newly prescribed")
  - Verifier recall check flagged 1 missed item (Claritin)
  - Escalation False (flagged fraction 1/9 ≈ 11%)
- **Action:** None. Milestone. Section 3.5 of the SOW is implemented.
- **Notes:** Full trace recorded per note. This is what the reviewer UI
  will display.

### Masker over-masking fixed

- **Severity:** medium (fixed 2026-10-09)
- **Where:** `src/masker.py`
- **What:** The masker was replacing drug names like "Nasonex" and
  "Ortho Tri-Cyclen" with X's because spaCy's NER occasionally
  classifies unusual capitalized words as PERSON. This weakened the
  verifier's judgment on those items (it saw "XXXXXXXXXXXXX" instead
  of the drug name).
- **Action:** Fixed by (1) correcting the `CLINICAL_BLOCKLIST` (it was
  accidentally one concatenated string due to missing commas), and
  (2) checking the blocklist inside the spaCy NER loop — if any token
  in the NER span matches a blocklist entry, the span is skipped.
- **Verified:** `CLINICAL_BLOCKLIST` now has 46 entries. On note_001,
  0 items are masked (correct — the note contains no true PII).
  Previously 2 drug names were being masked.
- **Notes:** This is a real correctness fix — it makes the verifier's
  input cleaner and improves its judgments on those items.

---

## 2026-10-13 — Day 5 (eval diagnosis and matcher fix)

### Cache provenance issue

- **Severity:** medium (deferred to pre-final-eval)
- **Where:** `src/extractor.py:86`, `src/verifier.py:44`
- **What:** The extractor and verifier cache keys were composed as `hash(model + SYSTEM_PROMPT + note)` and `hash(model + SYSTEM_PROMPT + note + items)`. They did NOT include `USER_PROMPT_TEMPLATE`. Editing `extractor_user.txt` or `verifier_user.txt` would silently reuse stale results.
- **Action:** Deferred. Fix is to add `USER_PROMPT_TEMPLATE` and a guardrails/schema fingerprint to both cache keys. Planned before the final eval.
- **Notes:** No incorrect numbers in the current 57-note eval, because neither user template changed during the period the cache was written. But the risk was live: any future prompt tuning would silently corrupt the next eval.

### Task A attempted and reverted

- **Severity:** high (fixed — reverted)
- **Where:** `src/extractor.py`, `src/prompts/extractor_system.txt`
- **What:** Attempted to shorten `name_as_written` via prompt rewrite ("shortest noun phrase" rule) and post-processing (`_clean_name` cutting at commas, " with ", " because of ", etc.). Result: diagnoses F1 0.720 → 0.664 (tp 197 → 169). Vitals also dropped from 0.403 to 0.252 (partly because the run skipped notes 017 and 033 on Groq 429, making the comparison unfair).
- **Action:** Reverted in commit `70bef15`. Kept the matcher changes from `223c01e` because those helped vitals.
- **Notes:** Root cause — the gold standard uses note-verbatim, often long entity names: `"Bilateral progressive conductive hearing losses with probable otosclerosis"`, `"status post lap band placement"`, `"Ligature B"`, `"Enlarging nevus 0.5 x 1 cm, left lower cheek"`. The prompt's GOOD/BAD examples biased the model toward short noun phrases that did not match gold. The `_clean_name` comma and " with " cuts also destroyed legitimate names.

### Matcher fix: abbreviation map and span containment

- **Severity:** high (fixed)
- **Where:** `src/eval/matching.py`
- **What:** The matcher compared names via exact string equality after lowercasing and whitespace collapse, and required span IoU ≥ 0.5. This failed whenever:
  - gold and prediction used abbreviations for the same vital ("Blood pressure" vs "BP", "Weight" vs "Wt")
  - one span was fully contained inside the other (gold `[805,811]` over the value vs predicted `[790,811]` over "blood pressure 124/78")
  - the name was identical but the spans overlapped by less than 50%
- **Action:** Fixed. Added `VITALS_ABBREVIATIONS` map (16 entries), `span_contains()` helper, `spans_overlap()` helper, and dropped the IoU threshold in `is_exact_match` from ≥0.5 to "any overlap".
- **Verified:** Vitals F1 went 0.144 → 0.403. Diagnoses, medications, procedures unchanged (their gap is not span-based).
- **Notes:** `is_partial_match` is now wired but not used as the default. It is available for future evaluation.

### Gold spans for vitals are inconsistent with the guideline

- **Severity:** medium (accepted, flagged)
- **Where:** `docs/labelling_guidelines.md` Section 4 vs `gold/note_*.json` vitals entries
- **What:** Section 4 defines spans for diagnoses only: "the span covers exactly the diagnosis text in the note". It does not state a span rule for vitals, medications, procedures, or allergies. The gold vitals spans therefore use a different convention: gold `"Blood pressure"` span `[805, 811]` covers `"124/78"` (the value), while the extractor spans the name.
- **Action:** Accepted. This is a labelling guideline gap, not an extractor bug. Flagged for the eval report. Matcher fix (containment) partially bridges the gap.
- **Notes:** Fixing properly requires either re-labelling gold vitals or updating the guideline. Out of scope for the current eval.

### Gold standard item counts (57 notes)

- **Severity:** note (informational)
- **Where:** `gold/note_*.json`
- **What:** Item counts across the 57 gold notes:
  - diagnoses 260, medications 134, procedures 108, allergies 8, vitals 74
  - Empty-list rates: allergies 50/57 empty, medications 22/57, procedures 12/57, vitals 34/57, diagnoses 4/57.
  - Specialty coverage: 15 specialties, 3–4 notes each.
  - ICD coverage: 243/260 diagnoses have an `icd_code`.
- **Action:** None. Baseline for the eval report.
- **Notes:** Allergy F1 = 1.000 is only meaningful at n=8; do not present it as a headline metric. ICD accuracy will be measured on 243 diagnoses, not 260.

### RAW vs VERIFIED on 57 notes

- **Severity:** high (finding)
- **Where:** `src/eval/run_eval.py`, both modes
- **What:** With the new matcher:


### ICD-10 confidence gate is not firing (critical)

- **Severity:** critical (SOW 3.3, 8.4b)
- **Where:** `src/icd_index.py`, function `icd_lookup`, lines ~210-213
- **What:** The confidence gate compares the top vector-search cosine
  against `MIN_COSINE_CONFIDENCE = 0.55`. Diagnostic on 7 queries
  (5 rare + 2 common) shows every query returns top_cosine between
  0.85 and 0.89, regardless of whether the top candidate is clinically
  related. Examples:
    - "ligature mark" (forensic) → Y652 "misadventures during surgical
      care", top_cosine 0.8611
    - "hyoid bone fracture" (neck) → S92211K "Displaced fracture of
      cuboid bone of right foot", top_cosine 0.8784
    - "hypertension" → I152 "Secondary hypertension", top_cosine 0.8834
  The gate never fires because no query falls below 0.55. The system
  returns codes for everything; the "no confident match" path is dead.
- **Root cause:** `bge-small-en` produces embeddings in a narrow angular
  cone for short clinical phrases. Cosine similarity does not
  discriminate between semantically related and unrelated clinical
  terms. The gate is comparing against the wrong signal.
- **Action:** Fix pending. Candidate fixes: (a) replace the cosine gate
  with a token-overlap gate (query tokens must appear in the top
  candidate's description); (b) strip the "Header: ... | Specific long
  description..." wrapper text from descriptions before indexing; (c)
  swap to a biomedical embedding model. (a) and (b) are cheap; (c)
  requires rebuilding 74,260 embeddings.
- **Notes:** The extraction eval reports diagnoses F1 0.720 because it
  measures name matching, not code matching. The coding track is
  broken and was not caught until `icd_eval.py` was built.

### ICD-10 "Other X" bias

- **Severity:** high (SOW 8.4a)
- **Where:** `src/icd_index.py`, `_rrf_fuse` output ordering
- **What:** Query "asthma" returns `J45998 "Other asthma"` as the top
  candidate instead of `J45.909 "Unspecified asthma"`. Both are in the
  J45 chapter, but the correct top-1 for an unqualified "asthma" query
  is the unspecified code. The ranking prefers "Other" because BM25
  matches the literal token "asthma" in the description of the
  "Other asthma" code.
- **Action:** Fix pending, tied to the description-wrapper strip.
- **Notes:** Top-1 accuracy will be low until this is addressed. Top-3
  accuracy may be acceptable (both candidates are in the top-3).

### BM25 scores are not discriminating

- **Severity:** medium (SOW 8.4a)
- **Where:** `src/icd_index.py`, `_bm25_search`
- **What:** BM25 candidate scores are in a very narrow range
  (0.016-0.033) across all queries, both common and rare. The
  description wrapper text ("Header: ... | Specific long description
  about this code: ...") introduces shared stopwords into every
  document, flattening the BM25 signal.
- **Action:** Fix pending, tied to the description-wrapper strip.

---