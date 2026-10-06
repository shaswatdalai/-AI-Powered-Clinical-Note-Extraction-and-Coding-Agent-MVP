# Timeline: Clinical Note Extraction and ICD-10 Coding Agent (MVP)

**Project start:** Tue 6 Oct 2026
**Review / sign-off:** Tue 6 Oct 2026, afternoon
**Code freeze:** Mon 13 Oct 2026, 6:00 PM
**Defense:** Tue 13 Oct 2026, evening

Each day ends with:
- A commit to the private repository
- An end-of-day update (done / blocked / next)
- The checkable output listed below

---

## Phase 0 — Understand and Design

| Day | Date | Work | Checkable output |
|---|---|---|---|
| Tue | 6 Oct (afternoon) | Final architecture + timeline + tech stack presented for sign-off | Sign-off received |

---

## Phase 1 — Data, Gold Standard, Extraction

| Day | Date | Work | Checkable output |
|---|---|---|---|
| Tue | 6 Oct | Ingestion + sectioning with offsets; Pydantic schema; labelling guidelines v1; label 12 notes | Offset tests pass; guidelines written; 12 gold notes |
| Wed | 7 Oct | Extractor on Groq with quote resolver and retry; ICD index (BM25 + Chroma) and RRF tool; label 15 notes | Extractor runs on 10 notes; ICD top-3 works; 27 gold notes |

Mid-point review with Zuhair on Wed 7 Oct per SOW section 10.

---

## Phase 2 — Verification and Agent

| Day | Date | Work | Checkable output |
|---|---|---|---|
| Wed | 8 Oct | Naive baseline; masker; injection shield; eval skeleton with matching rules; label 15 notes | Baseline numbers on labelled notes; 42 gold notes |
| Thu | 9 Oct | Verifier with contract, contradictions, recall check; label 15 notes | Verifier rejects planted fakes; 57 gold notes |
| Fri | 10 Oct | Orchestrator: plan, reconcile, bounded retry, abstain, escalate, trace, budget; label 15 notes | End-to-end run with trace JSON; 72 gold notes |
| Sat | 11 Oct | Reviewer UI; build contradiction, rare, adversarial sets; label 15 notes | UI works on 3 demo notes; 87 gold notes |

---

## Phase 3 — Evaluation, Documentation, Freeze

| Day | Date | Work | Checkable output |
|---|---|---|---|
| Sun | 12 Oct | Finish remaining gold labels; special sets finalized | 100 gold notes |
| Mon | 13 Oct | Full eval; report with 3+ failures; README; user guide; demo video; **freeze 6 PM** | One-command eval; report; video |
| Tue | 13 Oct (evening) | Present and defend | Slides on the six SOW sections |

---

## Riskiest pieces (scheduled early)

1. **Span resolver** (Tue 6 Oct) — every downstream display and metric depends on correct offsets
2. **ICD index + RRF** (Wed 7 Oct) — the retrieval layer
3. **Verifier independence** (Thu 9 Oct) — the SOW's central requirement

---

## Gold-standard labelling plan

- **Target:** 100 notes across 10+ specialties
- **Daily quota:** 12–15 notes
- **Running total:** 12 (Tue) → 27 (Wed) → 42 (Thu) → 57 (Fri) → 72 (Sat) → 87 (Sun) → 100 (Mon)
- **Fallback:** If the target is unreachable by Monday, reduce labelling scope in writing and document the reason in the evaluation report.

---

## Phase definitions (from SOW section 10)

- **Phase 0:** Understand and Design (Tue 6 Oct)
- **Phase 1:** Data, Gold Standard and Extraction (Tue 6 Oct – Wed 7 Oct)
- **Phase 2:** Verification and Agent (Wed 8 Oct – Sat 11 Oct)
- **Phase 3:** Evaluation, Documentation, Freeze (Sun 12 Oct – Mon 13 Oct)
- **Defense:** Tue 13 Oct