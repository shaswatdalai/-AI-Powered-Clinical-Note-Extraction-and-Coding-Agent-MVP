# Timeline: Clinical Note Extraction and ICD-10 Coding Agent (MVP)

**Project start:** Tue 6 Oct 2026
**Review / sign-off:** Tue 6 Oct 2026, afternoon
**Code freeze:** Mon 13 Oct 2026, 6:00 PM
**Defense:** Tue 13 Oct 2026

Each day ends with:
- A commit to the private repository
- An end-of-day update (done / blocked / next)
- The checkable output listed below

---

## Phase 0 — Understand and Design

| Day | Date | Work | Checkable output | Status |
|---|---|---|---|---|
| Tue | 6 Oct (afternoon) | Final architecture + timeline + tech stack presented for sign-off | Sign-off received | ✅ Done |

---

## Phase 1 — Data, Gold Standard, Extraction

| Day | Date | Work | Checkable output | Status |
|---|---|---|---|---|
| Tue | 6 Oct | Ingestion + sectioning with offsets; Pydantic schema; labelling guidelines v1; label 12 notes | Offset tests pass; guidelines written; 12 gold notes | ✅ Done |
| Wed | 7 Oct | Extractor on Groq with quote resolver and retry; ICD index (BM25 + Chroma) and RRF tool; label 15 notes | Extractor runs on 10 notes; ICD top-3 works; 27 gold notes | ✅ Done |

**Mid-point review with Zuhair on Wed 7 Oct per SOW section 10.** ✅ Done

---

## Phase 2 — Verification and Agent

| Day | Date | Work | Checkable output | Status |
|---|---|---|---|---|
| Wed | 8 Oct | Naive baseline; masker; injection shield; eval skeleton with matching rules; label 15 notes | Baseline numbers on labelled notes; 42 gold notes | ✅ Done |
| Thu | 9 Oct | Verifier with contract, contradictions, recall check; verifier integrated into eval; orchestrator; label 15 notes | Verifier rejects planted fakes; 57 gold notes | ⚠️ In progress |
| Fri | 10 Oct | Reviewer UI; build contradiction, rare, adversarial sets; label 15 notes | UI works on 3 demo notes; 72 gold notes | ⚠️ Planned |
| Sat | 11 Oct | Finish remaining gold labels; special sets finalized | 87–100 gold notes | ⚠️ Planned |

---

## Phase 3 — Evaluation, Documentation, Freeze

| Day | Date | Work | Checkable output | Status |
|---|---|---|---|---|
| Sun | 12 Oct | Full eval on all gold notes; report with 3+ failures; README; user guide; demo video; **freeze 6 PM** | One-command eval; report; video | ⚠️ Planned |
| Mon | 13 Oct (morning–evening) | Buffer / finish outstanding items | Final freeze | ⚠️ Planned |
| Tue | 13 Oct | Present and defend | Slides on the six SOW sections | ⚠️ Planned |

---

## Riskiest pieces (scheduled early)

1. **Span resolver** (Tue 6 Oct) — every downstream display and metric depends on correct offsets. ✅ Done
2. **ICD index + RRF** (Wed 7 Oct) — the retrieval layer. ✅ Done
3. **Verifier independence** (Thu 9 Oct) — the SOW's central requirement. ✅ Done

---

## Gold-standard labelling plan

- **Target:** 100 notes across 10+ specialties
- **Daily quota:** 12–15 notes
- **Actual running total:**
  - Tue 6 Oct: 12
  - Wed 7 Oct: 27
  - Thu 8 Oct: 42
  - Fri 9 Oct: 42 (labelling deferred; verifier + eval work consumed the day)
  - Sat 10 Oct: TBD — target 57+
  - Sun 11 Oct: TBD — target 72+
  - Mon 12 Oct: TBD — target 87+
  - Tue 13 Oct: TBD — target 100 (if reachable)
- **Fallback:** If the target is unreachable by Monday, reduce labelling scope in writing and document the reason in the evaluation report.

---

## Phase definitions (from SOW section 10)

- **Phase 0:** Understand and Design (Tue 6 Oct)
- **Phase 1:** Data, Gold Standard and Extraction (Tue 6 Oct – Wed 7 Oct)
- **Phase 2:** Verification and Agent (Wed 8 Oct – Sat 11 Oct)
- **Phase 3:** Evaluation, Documentation, Freeze (Sun 12 Oct – Mon 13 Oct)
- **Defense:** Tue 13 Oct

---