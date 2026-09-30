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
4. **Interactive Reviewer Cockpit:** High-performance FastAPI backend paired with a custom modern Glassmorphic web UI featuring real-time bidirectional span highlighting and full decision tracing.

---

## 📁 Repository Structure

```text
├── docs/
│   ├── architecture_design_document.md  # Formal Phase 0 System Design & Contracts
│   ├── day_by_day_timeline.md           # Milestone breakdown & daily deliverables
│   └── labelling_guidelines.md          # Annotation rules for 100-note Gold Standard
├── src/
│   ├── ingestion/                       # Note loading, sectioning, offset tracking
│   ├── extractor/                       # Pydantic schema validation & LLM extraction
│   ├── coding/                          # Hybrid BM25 + ChromaDB ICD-10 coding tool
│   ├── verifier/                        # Decoupled verification & contradiction detector
│   ├── orchestrator/                    # Agent planning, bounded retries, reconciliation
│   ├── guardrails/                      # Local PII masking & prompt injection defenses
│   └── ui/                              # FastAPI endpoints & Glassmorphic Reviewer UI
├── tests/
│   ├── evaluation/                      # Precision, Recall, F1, and Span Faithfulness harness
│   └── datasets/                        # Contradiction, Rare-Diagnosis, Adversarial test sets
├── data/
│   ├── raw/                             # Input clinical notes CSV and ICD-10 codebook
│   └── gold_standard/                   # Hand-labeled 100-note ground truth
├── .env.example                         # Environment variable template
├── .gitignore                           # Production gitignore rules
├── requirements.txt                     # Pinned project dependencies
└── README.md                            # Main project documentation
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Git

### 2. Installation
```bash
git clone <repo-url>
cd "AI-powered clinical documentation"
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and insert your free-tier API keys:
```bash
cp .env.example .env
```
- **Groq API Key:** [https://console.groq.com/keys](https://console.groq.com/keys)
- **Gemini API Key:** [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

---

## 📋 Statement of Work (SOW) Compliance

| Milestone | Target Window | Deliverables | Status |
|---|---|---|---|
| **Phase 0** | Sep 30 – Oct 1 | SOW review, Questions raised, Architecture Doc, Timeline, Sign-off | **Ready for Review** |
| **Phase 1** | Oct 2 – Oct 6 | Ingestion pipeline, Labeling guidelines, 100-note Gold Standard, Mid-point review | Planned |
| **Phase 2** | Oct 7 – Oct 8 | Verification engine, Contradiction detection, Agent orchestrator, Guardrails | Planned |
| **Phase 3** | Oct 9 – Oct 12 | Full evaluation harness, Reviewer cockpit UI, Demo video, Code freeze | Planned |
| **Phase 4** | Oct 13 | Live presentation & defense with Mirai Labs | Planned |

---

## 🛡️ License & Compliance
Built strictly in accordance with Mirai Labs Clinical Extraction Agent MVP Statement of Work (SOW). All rights reserved.
