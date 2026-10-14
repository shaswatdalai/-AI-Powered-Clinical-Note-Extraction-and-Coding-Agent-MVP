# Defense deck — outline

**SOW Section 11 structure. Six sections. Every design decision justified.**

## 1. Problem statement
- The client's manual coding workflow today.
- Why previous automated extraction attempts were rejected (fabrication).
- The design goal: extraction that can prove where every item came from.

## 2. Research
- Commercial: Nuance DAX, Amazon Comprehend Medical, Google Healthcare NLP, 3M 360.
- Open source: scispaCy, MedCAT, cTAKES, MedSpaCy.
- Papers: chain-of-verification, span-based NER, RAG for code lookup.
- What I took from each.

## 3. UI/UX and wireframing
- Reference products: GitHub code review, Bloomberg terminal, Linear.
- Why a two-pane layout with accept/reject per item.
- Why the trace viewer is a timeline, not a log.
- Screenshots of the current UI.

## 4. Execution
- Architecture diagram.
- Pipeline walk-through of one note.
- Extractor design (why Qwen, why Groq).
- Verifier design (why Gemini, why independent).
- ICD index design (why hybrid, why RRF).
- Orchestration (reconciliation, escalation, trace).

## 5. Current limitations
- Diagnoses F1 vs SOW target.
- Medications F1 vs SOW target.
- Procedures precision weakness.
- Vitals span convention.
- Verifier net effect on F1.
- Source data duplicate.
- Cost: Groq free-tier throttling.

## 6. Future scope
- Section-by-section extraction.
- Biomedical embedding model for the ICD index.
- Feedback loop from reviewer decisions.
- ICD hierarchical matching (chapter → category → code).
- Fine-tuning on the gold standard.