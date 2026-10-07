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

## 2026-10-07

### Extractor — note_001 divergences

- **Severity:** note (informational)
- **Where:** `src/extractor.py` running on `data/note_001.txt`
- **What:** Extractor returned 2 diagnoses, 5 medications, 2 vitals. Gold expects 3 diagnoses, 4 medications, 2 vitals.
  - Missing: "allergies" as a diagnosis. LLM treated it as a chief complaint, not a formal diagnosis.
  - Extra: 5 medications returned vs 4 in gold. Which item is extra — to be identified.
  - Correct: asthma `[520, 526]`, Allergic rhinitis `[1028, 1045]` — exact span match with gold.
- **Action:** Deferred. Assess across all 12 gold notes before deciding whether to adjust the extractor prompt.
- **Notes:** This is the kind of divergence the evaluation measures. It's a judgment call, not necessarily a bug.

### Masker — over-masking of "Allergic"

- **Severity:** high (fixed)
- **Where:** `src/masker.py`
- **What:** spaCy labelled "Allergic" (single token) as a PERSON entity. The masker replaced it with `XXXXXXXXX`, breaking extraction for "Allergic rhinitis".
- **Action:** Fixed on 2026-10-07. Added a `CLINICAL_BLOCKLIST` of clinical terms, and a rule to skip single-token entities (too many false positives). Masker now only masks multi-token names.
- **Notes:** Trade-off: names like "Cher" (single word) wouldn't be masked. Acceptable for clinical notes where names are usually "First Last" or "Dr. Last".

### Extractor — span covered evidence quote, not name

- **Severity:** high (fixed)
- **Where:** `src/extractor.py`, function `_build_extraction`
- **What:** The span resolver targeted the LLM's `evidence_quote`, which the LLM often returns as a full sentence. This produced spans much longer than the gold standard. Example: asthma span was `[506, 611]` (105 chars) instead of `[520, 526]` (6 chars).
- **Action:** Fixed on 2026-10-07. Span resolver now prefers the entity's canonical name (`name_as_written` for diagnoses, `name` for others), falling back to the evidence quote only when the name cannot be located.
- **Notes:** This is a design decision made explicit: the span represents the entity text, not the evidence context. Aligns with `ARCHITECTURE.md` Section 5 ("the span covers exactly the diagnosis text in the note").

### Groq API — 401 Unauthorized

- **Severity:** high (fixed)
- **Where:** `src/extractor.py`, initial run
- **What:** First API call to Groq returned 401 Unauthorized. Suspected the API key.
- **Action:** Fixed on 2026-10-07. Wrote `src/utils/check_groq.py` to isolate the issue. The key was valid, but the model ID was missing the `qwen/` provider prefix. Corrected `GROQ_MODEL` from `qwen-3.8-27b` to `qwen/qwen3.8-27b`.
- **Notes:** Groq's model IDs include a provider prefix. This is a common gotcha when switching between model providers. Future integrations should list `/models` first.



### ChromaDB batch size limit

- **Severity:** high (fixed)
- **Where:** `src/icd_index.py`, `build_index()`
- **What:** `collection.add()` with all 74,260 items at once failed with `ValueError: Batch size of 74260 is greater than max batch size of 5461`. ChromaDB has a per-call limit.
- **Action:** Fixed by chunking into batches of 5,000.
- **Notes:** This is a known limitation of the Rust-backed Chroma bindings. The Python docs don't prominently mention it. Worth remembering for any large-scale ingestion.

### ICD-10 description field contains wrapper text

- **Severity:** medium (deferred)
- **Where:** `src/icd_index.py`, descriptions loaded from `data/icd10cm_data.csv`
- **What:** The `description` column in the source CSV contains wrapper text:
  `Header: <parent> | Specific long description about this code: <actual>`
  This means the indexed descriptions include non-clinical tokens
  ("header", "specific", "long", "description"), which pollutes BM25
  scoring and embedding representation.
- **Action:** Deferred. Impact is minor — the correct code still ranks
  highly on test queries. To fix: strip the wrapper before indexing,
  keeping only the text after the last colon.
- **Notes:** Observed during ICD index build on 7 Oct. Would matter more
  if the description text were shown directly to the user without
  cleanup. The verifier sees this text, so a cleaner version improves
  the quality of its judgments.

### ChromaDB batch size limit

- **Severity:** high (fixed)
- **Where:** `src/icd_index.py`, `build_index()`
- **What:** `collection.add()` with all 74,260 items at once failed with
  `ValueError: Batch size of 74260 is greater than max batch size of 5461`.
  ChromaDB enforces a per-call batch limit.
- **Action:** Fixed by chunking into batches of 5,000.
- **Notes:** Known limitation of the Rust-backed Chroma bindings.

### End-to-end pipeline works on note_001

- **Severity:** note (success)
- **Where:** `src/utils/try_pipeline.py`, running on `data/note_001.txt`
- **What:** The pipeline ran cleanly: note → mask (2 items, same length) → extract (2 dx, 5 meds, 2 vitals) → ICD lookup.
- **Correct ICD chapter matches:**
  - asthma → J45.998, J45.902, J45.991
  - Allergic rhinitis → J30.89, J30.81, J30.9
- **Action:** None. Milestone.
- **Notes:** Diagnoses converged on correct ICD-10 chapters on first integration test. Specific sub-codes are for the verifier to refine.

### Autopsy notes over-extracted as diagnoses

- **Severity:** high (deferred — will fix on Day 3)
- **Where:** `src/extractor.py` running on `data/note_002.txt` (autopsy)
- **What:** The extractor returned 24 diagnoses for an autopsy note whose
  gold standard has 3. It treated every forensic finding (petechial
  hemorrhaging, injuries, lesions, pregnancy status, etc.) as a diagnosis.
  Root cause: the extractor prompt is written for clinical notes, not
  autopsy reports.
- **Action:** Deferred. Plan: detect autopsy specialty upfront, use a
  restricted prompt that extracts only the cause-of-death findings.
- **Notes:** The labelling guidelines already document that autopsy notes
  are handled differently. The extractor needs the same treatment. This
  is exactly the kind of failure the evaluation report should discuss.

### Groq 429 rate limit

- **Severity:** medium (fixed)
- **Where:** `src/extractor.py`, `_call_groq()` + `src/utils/eval_batch.py`
- **What:** Processing 12 notes back-to-back hit Groq's requests-per-minute
  limit. The extractor crashed with a hard error on note_003.
- **Action:** Fixed by (1) adding explicit 429 handling in `_call_groq()`
  that reads the `Retry-After` header and sleeps before retrying, and
  (2) adding a 2-second delay between notes in `eval_batch.py`.
- **Notes:** Free-tier Groq has ~30 RPM for Qwen. Pacing is necessary.
  This is a production-grade concern that will come up again during the
  full evaluation run.


  ### Extractor prompt fix — over-extraction resolved

- **Severity:** high (fixed 2026-10-07)
- **Where:** `src/prompts/extractor_system.txt`
- **What:** Initial extractor prompt over-extracted categories the SOW
  doesn't define as diagnoses (mechanism of injury, radiology findings,
  exam findings, social facts, autopsy findings). Worst case: 24 dx on
  the autopsy note vs a gold of 3.
- **Action:** Fixed by adding an explicit "DO NOT extract" list and an
  autopsy special case to the system prompt.
- **Verified:** After the fix, note_002 extracted 3 diagnoses (exact
  match with gold) and note_005 extracted 2 (exact match). Notes 001–005
  now show minor or no disagreements with gold.
- **Residual issues:**
  - note_001: "allergies" chief complaint not extracted as a diagnosis.
    LLM judgment call — defer.
  - note_003: "BMI is 38.5" extracted as a diagnosis instead of the
    implied condition (obesity). Prompt could be tightened further.
  - note_004: "restrictive element" extracted as a diagnosis; arguably
    a finding, not a diagnosis. Minor.

### Groq rate limits — worked around via smaller batches

- **Severity:** medium (mitigated)
- **Where:** `src/utils/eval_batch.py`
- **What:** Groq free-tier rate limits prevent processing 12+ notes in
  one session, especially at Qwen 3.8 27B's TPM limits.
- **Action:** Mitigated. Model processes in batches of 5, caches each
  response on disk, and can be resumed. A smaller, more structured
  prompt also reduced per-call token usage, which improves throughput.
- **Notes:** Free-tier constraints are part of the SOW. In production,
  a paid tier or a different model with higher limits would remove
  this bottleneck.

---