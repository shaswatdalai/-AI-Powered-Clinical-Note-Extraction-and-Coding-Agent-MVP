# Day-by-Day Project Timeline & Milestone Plan
## Clinical Note Extraction & Coding Agent MVP
**Document Version:** 1.0.0  
**Phase:** Phase 0 (Milestone Plan for Sign-off)  
**Candidate / Author:** Shaswat Kumar Dalai  
**Client / Reviewers:** Hemanth & Zuhair (Mirai Labs)  
**Project Window:** Wednesday, September 30 – Tuesday, October 13, 2026  

---

## 1. Overview & Strategy

This timeline breaks down the 10-working-day Statement of Work (plus planned weekend development acceleration) into daily deliverables, technical milestones, risk mitigations, and review checkpoints.

### Key Milestones & External Checkpoints:
- **Wed 30 Sep, 2:00 PM:** Scope & Clarification Questions delivered to Hemanth.
- **Thu 1 Oct, 4:00 PM:** Phase 0 Live Sign-Off Session with Hemanth.
- **Thu 1 Oct, 6:00 PM:** Architecture Document & Timeline formal submission deadline.
- **Tue 6 Oct (Time TBD):** Mid-Point Progress Review with Zuhair.
- **Mon 12 Oct, 6:00 PM:** Hard Code Freeze; Evaluation Report, README & Video submission.
- **Tue 13 Oct (Time TBD):** Final Defense & Live Demonstration Session.

---

## 2. Phase-by-Phase Detailed Schedule

### Phase 0: Understand & Design (Wed 30 Sep – Thu 1 Oct)
> **Rule:** *No feature code before sign-off.*

#### Day 0A: Wednesday, September 30, 2026
* **Objectives:** SOW dissection, environment preparation, Tier 1 questions dispatch.
* **Key Tasks:**
  - [x] Extract and analyze complete SOW requirements and 9 success criteria.
  - [x] Curate and submit Tier 1 clarification questions to Hemanth before 2:00 PM.
  - [x] Audit Python runtime (Python 3.14.3, Pip, Git, dependencies).
  - [x] Initialize Git repository, configure `.gitignore` and `requirements.txt`.
  - [x] Draft Architecture Design Document and Day-by-Day Timeline.
* **Deliverables:** Questions sent to Hemanth; Phase 0 documentation drafts.

#### Day 0B: Thursday, October 1, 2026
* **Objectives:** Architecture sign-off, live alignment session, final design approval.
* **Key Tasks:**
  - Incorporate any responses/feedback from Hemanth on data formats and assumptions.
  - Polish `docs/architecture_design_document.md` and `docs/day_by_day_timeline.md`.
  - **4:00 PM:** Attend Live Architecture Sign-Off review with Hemanth.
  - **6:00 PM:** Submit finalized architecture package to Mirai Labs.
* **Deliverables:** Approved Architecture Document, Approved Timeline, Sign-off recorded.

---

### Phase 1: Data Ingestion, Gold Standard & Extraction (Fri 2 Oct – Tue 6 Oct)

#### Day 1: Friday, October 2, 2026
* **Objectives:** Data ingestion pipeline, offset coordinate system, labeling guidelines.
* **Key Tasks:**
  - Ingest notes CSV (~5,000 clinical records) and ICD-10 code table CSV.
  - Build `src/ingestion/` module: UTF-8 normalization, section boundary detection.
  - Implement mathematical character offset coordinate tracker.
  - Write formal `docs/labelling_guidelines.md` for clinical entity annotation.
  - Share private GitHub repository with Mirai Labs collaborators.
* **Deliverables:** Working ingestion pipeline, offset verification test suite, labeling guidelines document.

#### Weekend Acceleration: Saturday, October 3, 2026
* **Objectives:** 50% Gold Standard completion + ICD-10 retrieval engine.
* **Key Tasks:**
  - Hand-annotate first 50 notes across 5 clinical specialties (diagnoses, medications, procedures, spans, statuses, gold ICD-10 codes).
  - Build `src/coding/` module: Ingest ICD-10 codebook into BM25 index and ChromaDB vector store.
  - Implement Reciprocal Rank Fusion (RRF) and confidence thresholding ($0.70$ cutoff).
* **Deliverables:** 50 hand-labeled gold standard notes; functional ICD-10 hybrid search tool.

#### Weekend Acceleration: Sunday, October 4, 2026
* **Objectives:** 100% Gold Standard completion + Naive baseline runner.
* **Key Tasks:**
  - Hand-annotate remaining 50 notes across next 5+ clinical specialties (Total $\ge 100$ notes across $\ge 10$ specialties).
  - Serialize gold standard into `data/gold_standard/gold_standard_100.json`.
  - Implement single-prompt Naive Baseline extractor without verification pass.
  - Run baseline against 100-note gold standard to establish benchmark F1 scores.
* **Deliverables:** 100-note gold standard dataset; baseline evaluation numbers.

#### Day 2: Monday, October 5, 2026
* **Objectives:** Production Structured Extractor & Span Enforcer.
* **Key Tasks:**
  - Implement `src/extractor/` with Pydantic V2 structured outputs via Groq Llama 3.3 70B.
  - Wire extractor to ICD-10 coding tool for automated diagnostic code proposals.
  - Implement strict programmatic span faithfulness verification ($T[start:end] == exact\_text$).
  - Measure Extractor precision/recall vs. Naive Baseline on initial gold subset.
* **Deliverables:** Working structured extractor producing verified offsets.

#### Day 3: Tuesday, October 6, 2026
* **Objectives:** Mid-Point Review with Zuhair + Benchmark Validation.
* **Key Tasks:**
  - Prepare demonstration for Zuhair: Note ingestion, section splitting, structured extraction, ICD-10 lookup, and baseline metrics.
  - **Mid-Point Review Session:** Present progress, demonstrate offset faithfulness, solicit feedback.
  - Commit Day 3 progress to private GitHub repo.
* **Deliverables:** Mid-point review completed; Phase 1 signed off.

---

### Phase 2: Verification Engine & Agent Orchestration (Wed 7 Oct – Thu 8 Oct)

#### Day 4: Wednesday, October 7, 2026
* **Objectives:** Independent Verification Engine & Contradiction Detection.
* **Key Tasks:**
  - Implement `src/verifier/` using decoupled Google Gemini 2.0 Flash pass.
  - Implement asymmetric payload builder (verifier sees only raw note + candidate items; no extractor reasoning).
  - Implement multi-section internal contradiction detection engine.
  - Implement missed-entity discovery (recall gap analyzer).
* **Deliverables:** Working independent verifier detecting hallucinations, status errors, and planted contradictions.

#### Day 5: Thursday, October 8, 2026
* **Objectives:** Agent State Machine Orchestrator & Guardrails.
* **Key Tasks:**
  - Implement `src/orchestrator/` dynamic agent loop: Planning $\to$ Extraction $\to$ Coding $\to$ Verification $\to$ Arbitration.
  - Implement bounded retry mechanism ($N \le 2$) for target reconciliation.
  - Implement abstention and human-escalation logic.
  - Implement `src/guardrails/`: Local PII anonymizer and XML prompt injection shields.
  - Full structured JSON audit logging per note.
* **Deliverables:** Complete autonomous agent pipeline with full execution tracing and safety guardrails.

---

### Phase 3: Evaluation, Reviewer Interface & Polish (Fri 9 Oct – Mon 12 Oct)

#### Day 6: Friday, October 9, 2026
* **Objectives:** Adversarial Datasets & Full Evaluation Harness.
* **Key Tasks:**
  - Construct 3 specialized test datasets:
    1. Contradiction Set: $\ge 20$ clinical notes with verified planted contradictions.
    2. Rare-Diagnosis Set: $\ge 10$ notes with absent/atypical diagnoses.
    3. Adversarial Set: $\ge 10$ notes with prompt injection commands & residual PII.
  - Implement `tests/evaluation/eval_harness.py`: Automated scoring of Precision, Recall, F1, Span Faithfulness (100%), Status Correctness, ICD-10 Top-1/Top-3, Latency, and Cost.
  - Run comprehensive evaluation suite and record comparative metrics.
* **Deliverables:** Full automated test suite; completed evaluation runs across all datasets.

#### Weekend Polish: Saturday 10 Oct – Sunday 11 Oct, 2026
* **Objectives:** Reviewer Cockpit Interface (FastAPI + Glassmorphic Web UI).
* **Key Tasks:**
  - Implement FastAPI backend serving clinical notes, extraction records, and trace logs.
  - Build modern Glassmorphic Reviewer UI:
    - Interactive note viewer with color-coded bidirectional span highlights.
    - Structured entity table with one-click Accept/Reject toggles.
    - High-contrast Flagged Items & Contradictions panel.
    - Live Agent Step-by-Step Decision Trace viewer.
    - One-click JSON export.
* **Deliverables:** Fully interactive, responsive Reviewer Dashboard running on localhost.

#### Day 7: Monday, October 12, 2026
* **Objectives:** Evaluation Report, Demo Video & Code Freeze.
* **Key Tasks:**
  - Write comprehensive `docs/evaluation_report.md` detailing:
    - All 9 success criteria results.
    - Baseline vs. Agent comparison tables.
    - Honest root-cause analysis of $\ge 3$ concrete failure cases.
  - Write `README.md` with foolproof single-command setup (`pip install -r requirements.txt && python app.py`).
  - Record 5–8 minute professional demo video (Clean note, Contradictory note, Rare diagnosis, Evaluation harness run).
  - Perform clean-room installation test in fresh virtual environment.
  - **6:00 PM:** HARD CODE FREEZE. Final commit pushed to GitHub.
* **Deliverables:** Final repository ready, Evaluation Report, README, Demo Video.

---

### Phase 4: Presentation & Live Defense (Tuesday, October 13, 2026)

#### Day 8: Tuesday, October 13, 2026
* **Objectives:** Live defense, technical Q&A, and MVP demonstration.
* **Key Tasks:**
  - Live walkthrough of the Reviewer Interface on localhost.
  - Defense of architectural decisions (two-model asymmetry, hybrid ICD search, bounded arbitration).
  - Walkthrough of failure case analysis and honesty evaluation.
* **Deliverables:** Project completion & candidate selection.

---

## 3. Risk Matrix & Proactive Mitigations

| Identified Risk | Severity | Proactive Mitigation Strategy |
|---|---|---|
| **Free-Tier Rate Limits (Groq / Gemini 429)** | High | Leaky-bucket client-side rate limiting, exponential backoff with random jitter, local response disk caching for repeat notes. |
| **Span Drift (Off-by-one string mismatch)** | Critical | Strict coordinate slicing verification ($T[start:end] == exact\_text$) prior to emitting any entity. Discard Paraphrases. |
| **Annotation Bottleneck (100 notes hand-labeled)** | Medium | Dedicated weekend timeblocks (Oct 3–4); standardized annotation template; prioritized multi-specialty sampling. |
| **Ambiguous ICD-10 Descriptions** | Medium | Hybrid BM25 lexical + dense semantic retrieval; conservative $0.70$ threshold with explicit "no confident match" path. |
| **Reviewer UI Latency** | Low | Lightweight Vanilla HTML/CSS/JS frontend communicating via asynchronous FastAPI endpoints; instant DOM rendering. |
