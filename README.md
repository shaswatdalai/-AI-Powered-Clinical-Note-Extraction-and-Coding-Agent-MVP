# README

**AI-Powered Clinical Note Extraction & Coding Agent — MVP**

An agent that reads free-text clinical notes, extracts structured medical entities (diagnoses, medications, procedures, allergies, vitals), maps diagnoses to ICD-10 codes via hybrid retrieval, verifies every extracted item with an independent second model, and flags anything it cannot prove for human review.

Built for the Mirai Labs SOW (Clinical Note Extraction and ICD-10 Coding Agent MVP).

---

## Overview

Medical coding staff read clinical notes by hand and turn them into structured records with ICD-10 codes for billing. This work is slow, error-prone, and previous attempts at automation hallucinated — they invented findings that were not in the note. This system addresses that problem by making every accepted item *provable*.

Every accepted extraction carries:

- A **verbatim quote** from the source note
- A **character span** `[start, end]` into the original note
- A **verdict** from an independent verifier model (different family from the extractor)

Anything that cannot be proven — or that fails verification — is flagged with a reason for human review. Nothing is accepted silently.

---

## Design principles

1. **Fail closed.** Uncertain, broken, or unverified → flag for review, never accept.
2. **Offsets are the single source of truth.** Every highlight, export, and metric is computed from character offsets into the original note.
3. **Code checks the LLM, not the other way around.** Span existence, schema shape, status values, and thresholds are enforced in plain code.
4. **Independence.** Extractor and verifier are separate models with a written contract. The verifier never sees the extractor's reasoning.
5. **The LLM never sees a dataset.** The extractor sees one masked note per call. The verifier sees one masked note + the extractor's items. The ICD code table is never sent to any model in bulk.
6. **Reproducible.** Temperature 0, cached model responses, one-command evaluation.

---

## Architecture at a glance

```
Raw clinical note
   │
   ▼
Sectioner         → detects headings, records offsets
   │
   ▼
PII Masker        → regex + spaCy, same-length replacement
   │
   ▼
Injection Shield  → delimiter wrapping + system instruction
   │
   ▼
Extractor LLM     → Qwen 3.8 27B (Groq) → JSON with verbatim quotes
   │
   ▼
Span Resolver     → code computes character offsets from quotes
   │
   ▼
ICD Lookup        → BM25 + ChromaDB + RRF → top-3 candidates or NO_CONFIDENT_MATCH
   │
   ▼
Verifier LLM      → Gemini 3.5 Flash Lite → SUPPORTED / REJECTED per item
   │
   ▼
Reconcile         → ACCEPT (both agree) or FLAG (disagreement)
   │
   ▼
Reviewer UI + trace + audit log
```

Full design in [`ARCHITECTURE.md`](./ARCHITECTURE.md). Technology choices and rejected alternatives in [`TECH_STACK.md`](./TECH_STACK.md).

---

## Repository structure

```
.
├── ARCHITECTURE.md              Full system design and decisions
├── TIMELINE.md                  Day-by-day plan and current status
├── TECH_STACK.md                Tech choices + rejected alternatives
├── README.md                    This file
├── requirements.txt             Python dependencies
├── conftest.py                  Pytest project root marker
├── .env.example                 Environment variable template
├── .gitignore
├── data/
│   ├── mtsamples.csv            ~5,000 clinical notes (source)
│   ├── icd10cm_data.csv         ~74,260 ICD-10 codes (source)
│   ├── note_001.txt … note_042.txt       Selected notes for gold labelling
│   └── note_*.meta.json         Metadata sidecars
├── docs/
│   ├── labelling_guidelines.md  Rules for hand-labelling gold notes
│   ├── FINDINGS.md              Running log of issues and fixes
│   └── eval_baseline.md         Evaluation metrics across stages
├── gold/
│   └── note_001.json … note_042.json     Hand-labelled gold annotations
├── src/
│   ├── schema.py                Pydantic models (extraction + verifier contracts)
│   ├── sectioner.py             Section detection with offset preservation
│   ├── masker.py                PII masking (regex + spaCy, same-length)
│   ├── guardrails.py            Injection shield (delimiter wrapping)
│   ├── extractor.py             Extractor LLM caller + span resolver
│   ├── icd_index.py             Hybrid BM25 + ChromaDB + RRF
│   ├── verifier.py              Verifier LLM caller (fail-closed)
│   ├── orchestrator.py          Agent loop: extract → ICD → verify → reconcile
│   ├── prompts/
│   │   ├── extractor_system.txt
│   │   ├── extractor_user.txt
│   │   ├── verifier_system.txt
│   │   └── verifier_user.txt
│   ├── eval/
│   │   ├── matching.py          Exact / partial matching, P/R/F1
│   │   └── run_eval.py          One-command evaluation
│   └── utils/
│       ├── select_notes.py      Note selection for gold labelling
│       ├── find_spans.py        Helper for computing spans
│       ├── verify_gold.py       Assert every gold span slices correctly
│       ├── check_groq.py        Groq API key + model availability check
│       ├── try_extractor.py     Smoke test: extractor on one note
│       ├── try_verifier.py      Smoke test: extract + ICD + verify on one note
│       ├── try_pipeline.py      End-to-end smoke test
│       └── eval_batch.py        Run pipeline on all gold notes
└── tests/
    ├── test_schema.py
    ├── test_sectioner.py
    ├── test_masker.py
    ├── test_extractor.py
    ├── test_verifier.py
    ├── test_guardrails.py
    └── test_icd.py
```

---

## Quick start

### 1. Prerequisites

- Python 3.10+
- Git
- A Groq API key (https://console.groq.com/keys) — free tier
- A Google AI Studio key (https://aistudio.google.com/app/apikey) — free tier

### 2. Installation

```bash
git clone <repo-url>
cd "AI-powered clinical documentation"
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Environment configuration

Copy `.env.example` to `.env` and fill in:

```
GROQ_API_KEY=<your_groq_key>
GOOGLE_API_KEY=<your_google_ai_studio_key>
```

### 4. Build the ICD index

```bash
python -m src.icd_index --build
```

Reads `data/icd10cm_data.csv`, builds BM25 + ChromaDB indexes, persists to disk. Takes ~17 minutes on CPU (encoding 74,260 descriptions). Subsequent loads take ~7 seconds.

### 5. Run the pipeline on one note

```bash
python -m src.utils.try_pipeline
```

Runs note → mask → extract → ICD lookup on `data/note_001.txt`.

### 6. Run the full evaluation

```bash
# Raw extractor (no verifier)
python -m src.eval.run_eval 42 60

# With verifier applied
python -m src.eval.run_eval 42 60 --verify
```

First number is the note limit; second is the pacing in seconds (for rate-limit safety on free tiers). Cached notes process instantly.

---

## Requirements from the SOW (compliance summary)

| SOW section | Requirement | Status |
|---|---|---|
| 3.1 | Note ingestion and sectioning with offset preservation | ✅ Implemented |
| 3.2 | Structured extraction with enforced schema and mandatory spans | ✅ Implemented |
| 3.3 | ICD-10 hybrid retrieval tool with no-confident-match path | ✅ Implemented |
| 3.4 | Independent verification agent with contradictions and recall check | ✅ Implemented |
| 3.5 | Agent orchestration with reconciliation, retries, escalation, trace | ✅ Implemented |
| 3.6 | Reviewer interface | ⚠️ In progress |
| 3.7 | Gold standard of 100 hand-labelled notes | ⚠️ 42/100 and growing |
| 3.8 | Guardrails: no fabrication, PII masking, injection resistance | ✅ Implemented (adversarial test set pending) |
| 3.9 | Evaluation harness with metrics, baseline, special sets | ⚠️ Metrics implemented; special sets pending |

---

## Current metrics

Raw extractor, 42 gold notes (no verifier applied):

| Entity | Precision | Recall | F1 |
|---|---|---|---|
| Diagnoses | 0.655 | 0.800 | 0.720 |
| Medications | 0.550 | 0.635 | 0.589 |
| Procedures | 0.429 | 0.698 | 0.531 |
| Vitals | 0.147 | 0.167 | 0.156 |

Verifier applied, 5 notes (category check active):

| Entity | Precision | Recall | F1 |
|---|---|---|---|
| Diagnoses | 0.778 | 0.583 | 0.667 |
| Medications | 0.667 | 0.667 | 0.667 |

Full baseline and gap analysis in [`docs/eval_baseline.md`](./docs/eval_baseline.md).

---

## Known limitations

- **Vitals extraction is weak** — F1 ≈ 0.16 on the current baseline. Both over- and under-extraction. Extractor prompt needs tighter vitals rules.
- **Procedures precision is weak** — extractor over-produces procedures from routine exam components.
- **Free-tier rate limits constrain batch evaluation** — pacing is required. Caching makes reruns free.
- **Verifier category check does not yet cover procedures or vitals** — only diagnoses and medications.
- **Gold standard is not yet complete** — currently at 42 notes; the target is 100.
- **No adversarial test set yet** — SOW Section 3.9 requires notes with embedded instructions and protected info.

Detailed per-item analysis in [`docs/FINDINGS.md`](./docs/FINDINGS.md).

---

## Compliance and confidentiality

The repository is private and shared only with the Mirai Labs reviewers. Model choices and configurations respect the SOW's constraint of free-tier APIs only. See `.env.example` for the required keys (no keys are committed).



## Running with multiple workers

The interface runs single-worker by default because the SOW assumes a
single reviewer session at a time (Section 7.2).

To run with multiple workers (e.g. for multiple concurrent reviewers):

    uvicorn src.ui.app:app --workers 2 --port 8000

Caveat: each worker process loads its own copy of the ICD index
(BM25 + ChromaDB + embeddings, roughly 250 MB resident). On a laptop,
2 workers is the practical ceiling before you start swapping.

## Caching

Two layers of caching keep repeated runs fast:

1. **On-disk LLM cache** in `cache/extractor/` and `cache/verifier/`.
   Every LLM response is keyed by
   `hash(model + system prompt + user prompt template + guardrails/schema
   fingerprint + input)`. Re-running the same note with the same code is
   a disk read, not an API call. Editing a prompt invalidates the cache
   for every note the prompt touches.

2. **Provider-side prefix caching.** The extractor and verifier system
   prompts are constant across notes. Groq and Google both cache the
   prompt prefix server-side, so only the note text is transmitted per
   call after the first. This is enabled implicitly by the provider when
   the prefix is long enough.

To force a clean slate:

    Remove-Item -Recurse -Force cache/extractor, cache/verifier



## Redis result cache

The reviewer interface uses Redis as a whole-note result cache:

- Redis server on `localhost:6379` (Memurai on Windows, or the standard
  Redis package on Linux/macOS).
- Every pipeline result is stored under
  `pipeline:<sha256(note_id | prompt_hash | note_text)>` with a 24-hour TTL.
- Running the same note again is instant — it hits Redis instead of
  re-invoking the LLM.
- Editing any prompt invalidates every cached result automatically (the
  prompt hash is part of the key).
- If Redis is unreachable, the interface falls back to running the
  pipeline normally with no error.

Inspect the cache from the UI: the hit-rate indicator in the top bar
updates every 3 seconds. Or query it directly:

    curl http://localhost:8000/api/cache/stats

Clear the cache (does not touch reviewer decisions):

    curl -X POST http://localhost:8000/api/cache/reset

### Install on Windows

Download and install Memurai Developer Edition from
`https://www.memurai.com/get-memurai`. It installs as a Windows service
and starts on port 6379 automatically. Verify with:

    python -c "import redis; print(redis.Redis().ping())"

## Running with multiple workers

The interface runs single-worker by default because SOW 7.2 assumes a
single reviewer session at a time.

For multiple concurrent reviewers:

    uvicorn src.ui.app:app --workers 2 --port 8000

Each worker loads its own copy of the ICD index (~250 MB resident), so
2 workers is the practical ceiling on a laptop. The Redis result cache
is shared across workers, so cross-worker cache hits work as expected.

The reviewer accept/reject decisions are stored per-worker in memory
and are NOT shared. If you need shared decisions, move
`_reviewer_decisions` into Redis (a small follow-up).


---