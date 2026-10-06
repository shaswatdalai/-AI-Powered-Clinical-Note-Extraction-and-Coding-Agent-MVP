# AI-Powered Clinical Note Extraction & Coding Agent MVP

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic V2](https://img.shields.io/badge/Validation-Pydantic%20V2-e92063.svg)](https://docs.pydantic.dev/)
[![ChromaDB](https://img.shields.io/badge/VectorStore-ChromaDB-purple.svg)](https://www.trychroma.com/)
[![Architecture Approved](https://img.shields.io/badge/Phase%200-Design%20Ready-success.svg)]()

> **Autonomous, zero-fabrication clinical documentation agent that ingests raw EHR notes, performs span-anchored structured entity extraction, maps diagnoses to ICD-10 via hybrid lexical/semantic retrieval, runs decoupled adversarial verification, and reconciles conflicts.**

---

## 🏥 Project Overview

In clinical note processing and medical coding, **unverified hallucination is a critical patient safety and legal hazard**. This project solves that via an **asymmetric multi-agent architecture**:

1. **100% Span Faithfulness:** Every extracted entity (diagnoses, medications, procedures, allergies, vitals) is strictly anchored to verbatim character offsets in the original note. Unanchored items are programmatically discarded.
2. **Decoupled Verification:** A secondary LLM pass independently audits candidate entities without visibility into the extractor's reasoning scratchpad, catching status misattributions, negations, and planted contradictions.
3. **Hybrid ICD-10 Retrieval:** Combines BM25 lexical keyword matching with ChromaDB dense semantic vector search under Reciprocal Rank Fusion (RRF), yielding top-3 candidate codes or an explicit `"no confident match"`.
4. **Interactive Reviewer Cockpit:** FastAPI backend paired with a lightweight browser UI featuring span highlighting and full decision tracing.

---

## 📁 Repository Structure

```text
├── docs/
│   ├── ARCHITECTURE.md              # System design, contracts, decisions
│   ├── TIMELINE.md                  # Day-by-day plan and deliverables
│   ├── TECH_STACK.md                # Tech choices + rejected alternatives
│   └── labelling_guidelines.md      # Annotation rules for the 100-note Gold Standard
├── src/
│   ├── prompts/                     # Prompt templates (system + user)
│   ├── utils/                       # Shared helpers
│   ├── schema.py                    # Pydantic extraction schema
│   ├── sectioner.py                 # Note ingestion, section detection, offset tracking
│   ├── masker.py                    # Local PII masking (regex + spaCy)
│   ├── extractor.py                 # Groq Qwen 3.8 27B caller + span resolver
│   ├── icd_index.py                 # Hybrid BM25 + ChromaDB ICD-10 retrieval
│   ├── verifier.py                  # Gemini 3.8 Flash independent verification
│   ├── orchestrator.py              # Agent loop, retries, reconciliation, budget
│   └── ui/                          # FastAPI endpoints + reviewer interface
├── tests/
│   ├── test_schema.py
│   ├── test_sectioner.py
│   ├── test_masker.py
│   ├── test_extractor.py
│   ├── test_icd.py
│   ├── test_verifier.py
│   └── test_orchestrator.py
├── data/
│   ├── mtsamples.csv                # Clinical notes (~5,000 rows)
│   ├── icd10cm_data.csv             # ICD-10-CM code table (~74,000 rows)
│   └── note_*.txt                   # Per-note excerpts used for gold labelling
├── gold/                            # Hand-labelled 100-note gold standard
├── results/                         # Per-note JSON outputs and traces (gitignored)
├── .env.example                     # Environment variable template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Start

### 1. Prerequisites

- Python 3.10+
- Git

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

### 3. Environment Configuration

Copy `.env.example` to `.env` and insert your free-tier API keys:

```bash
cp .env.example .env
```

- **Groq API key (extractor, Qwen 3.8 27B):** https://console.groq.com/keys
- **Google AI Studio key (verifier, Gemini 3.8 Flash):** https://aistudio.google.com/app/apikey

### 4. Build the ICD index

```bash
python -m src.icd_index --build
```

This reads `data/icd10cm_data.csv`, builds the BM25 index and ChromaDB collection, and persists both to `chroma_db/` and `bm25_index.pkl`.

### 5. Run the reviewer UI

```bash
uvicorn src.ui.app:app --reload
```

Then open `http://localhost:8000`.

---

## 📋 SOW Compliance

| Milestone | Target Window | Deliverables | Status |
|---|---|---|---|
| **Phase 0** | Wed 30 Sep – Tue 6 Oct | SOW review, questions raised, architecture doc, timeline, tech stack, sign-off | **Sign-off requested** |
| **Phase 1** | Wed 7 Oct – Thu 8 Oct | Ingestion pipeline, labelling guidelines, Pydantic schema, extractor, ICD index, first 27 gold notes, mid-point review | Planned |
| **Phase 2** | Fri 9 Oct – Mon 12 Oct | Naive baseline, masker, injection shield, verifier, orchestrator, eval skeleton, up to 87 gold notes | Planned |
| **Phase 3** | Tue 13 Oct | Full evaluation harness, reviewer cockpit UI, demo video, README, freeze 6 PM | Planned |
| **Phase 4** | Wed 14 Oct | Live presentation & defense with Mirai Labs | Planned |

---

## 🔑 Key Design Decisions

- **LLM never sees a dataset.** One masked note per prompt. The ICD-10 code table is never sent to any model — only the top-3 candidates per diagnosis.
- **Quotes, not offsets, from the LLM.** The extractor returns verbatim `evidence_quote` strings. Code resolves those to `[start, end]` offsets against the original note. Offsets are the single source of truth for all downstream display, export, and metrics.
- **Two independent model families.** Extractor is Groq Qwen 3.8 27B. Verifier is Gemini 3.8 Flash. Different training data → decorrelated errors. Enforced by prompt isolation: the verifier never sees the extractor's reasoning.
- **Fail closed.** If a span does not resolve, if the verifier rejects, if the pipeline errors — the item is flagged for human review, never accepted silently.
- **Reproducible evaluation.** Temperature 0, all model responses cached on disk keyed by `hash(model + prompt + schema_version)`, one-command eval, gold standard frozen before prompt tuning.

---

## 🛡️ License & Compliance

Built strictly in accordance with the Mirai Labs Clinical Extraction Agent MVP Statement of Work. All rights reserved.