# Timeline: Clinical Note Extraction and ICD-10 Coding Agent (MVP)

**Project duration:** Wed 30 Sep 2026 → Thu 15 Oct 2026 (11 working days, one Sunday off)
**Review / sign-off:** Tue 6 Oct 2026, afternoon
**Code freeze:** Wed 14 Oct 2026, 6:00 PM
**Defense:** Thu 15 Oct 2026

Each day ends with:
- A commit to the private repository
- An end-of-day update (done / blocked / next)
- The checkable output listed below

---

## Phase 0 — Understand and Design

| Day | Date | Work | Checkable output |
|---|---|---|---|
| Wed | 30 Sep | Read SOW; list every question; share private repo | Questions sent |
| Thu | 1 Oct | Architecture v1 draft; initial timeline | Architecture doc v1 submitted |
| Tue | 6 Oct (afternoon) | Final architecture + timeline + tech stack presented for sign-off | Sign-off received |

---

## Phase 1 — Data, Gold Standard, Extraction

| Day | Date | Work | Checkable output |
|---|---|---|---|
| Wed | 7 Oct | Ingestion + sectioning with offsets; Pydantic schema; labelling guidelines v1; label 12 notes | Offset tests pass; guidelines written |
| Thu | 8 Oct | Extractor on Groq with quote resolver and retry; ICD index (BM25 + Chroma) and RRF tool; label 15 notes | Extractor runs on 10 notes; ICD top-3 works |

Mid-point review with Zuhair on Wed 7 Oct per SOW section 10.

---

## Phase 2 — Verification and Agent

| Day | Date | Work | Checkable output |
|---|---|---|---|
| Fri | 9 Oct | Naive baseline; masker; injection shield; eval skeleton with matching rules; label 15 notes | Baseline numbers on labelled notes |
| Sat | 10 Oct | Verifier with contract, contradictions, recall check; label 15 notes | Verifier rejects planted fakes |
| Mon | 12 Oct | Orchestrator: plan, reconcile, bounded retry, abstain, escalate, trace, budget; label 15 notes | End-to-end run with trace JSON |
| Tue | 13 Oct | Reviewer UI; build contradiction, rare, adversarial sets; label 15 notes | UI works on 3 demo notes |

---

## Phase 3 — Evaluation, Documentation, Freeze

| Day | Date | Work | Checkable output |
|---|---|---|---|
| Wed | 14 Oct | Full eval; report with 3+ failures; README; user guide; demo video (5–8 min); **freeze 6 PM** | One-command eval; report; video |
| Thu | 15 Oct | Present and defend | Slides on the six SOW sections |

---

## Riskiest pieces (scheduled early)

1. **Span resolver** (Wed 7 Oct) — every downstream display and metric depends on correct offsets
2. **ICD index + RRF** (Thu 8 Oct) — the retrieval layer
3. **Verifier independence** (Sat 10 Oct) — the SOW's central requirement

---

## Gold-standard labelling plan

- **Target:** 100 notes across 10+ specialties
- **Daily quota:** 12–15 notes
- **Running total:** 12 (Wed) → 27 (Thu) → 42 (Fri) → 57 (Sat) → 72 (Mon) → 87 (Tue) → 100 (Wed, if needed)
- **Fallback:** If the target is unreachable by Tuesday, reduce labelling scope in writing and document the reason in the evaluation report.

---

## Phase definitions (from SOW section 10)

- **Phase 0:** Understand and Design (Wed 30 Sep – Tue 6 Oct)
- **Phase 1:** Data, Gold Standard and Extraction (Wed 7 Oct – Thu 8 Oct)
- **Phase 2:** Verification and Agent (Fri 9 Oct – Tue 13 Oct)
- **Phase 3:** Evaluation, Documentation, Freeze (Wed 14 Oct)
- **Defense:** Thu 15 Oct