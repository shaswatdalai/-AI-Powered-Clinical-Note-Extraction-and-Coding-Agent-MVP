# Defense deck — outline

**SOW Section 11 structure. Six sections. Every design decision justified.
"Every piece of the technology stack and every design decision must be
justified; 'it was the default' is not an answer."**

---

## Section 1 — Problem statement

**The client's manual coding workflow today.**
- Clinical coders read each note by hand, transcribe findings into
  structured records, and look up ICD-10 codes manually.
- Slow, costly, and disagreeable — coders reach different codes for the
  same note.
- Errors propagate into billing and patient records.

**Why previous automated extraction was rejected.**
- Earlier tools invented findings that were not in the note.
- The client's requirement is not just extraction — it is extraction that
  can prove *where* every item came from, and that abstains when it is
  not sure.

**The design goal.**
- Extract structured items with mandatory character spans.
- Verify every item against the source text independently.
- Abstain and flag rather than guess.
- Never fabricate. A single unsupported item fails the contract.

---

## Section 2 — Research

**Commercial systems studied.**
- **Nuance DAX** — ambient clinical documentation; broad scope,
  clinician-facing, not coder-facing. Did not solve provenance.
- **Amazon Comprehend Medical** — entity extraction with an
  ICD-10-CM linking API. Closed-source black box; no independent
  verification pass.
- **Google Healthcare NLP** — medical entity extraction with FHIR
  mapping. Requires GCP setup; no confidence-based abstention path.
- **3M 360 Encompass / Optum** — production coder workflows. No public
  API; too heavyweight for an MVP scope.

**Open-source and research.**
- **scispaCy** and **MedCAT** — biomedical NER models. Chose not to use
  them: clinical text from MTSamples contains abbreviations and dictation
  artefacts that general biomedical NER models miss. LLM extraction with
  structured output handled this better.
- **cTAKES** — rule-based clinical NLP. Too rigid for the diversity of
  note formats across 26 specialties.
- **Chain-of-verification (CoVe)** — the paper that inspired the
  independent-verifier design. Two-pass architecture with a second model
  checking the first model's output.
- **Span-based NER literature** — the pattern of returning spans rather
  than free text. We enforce spans at the schema level.
- **RAG for code lookup** — the pattern of retrieving candidate codes
  from a table rather than generating them. Implemented as BM25 + vector
  search + RRF over the ICD-10 code table.

**What I took from each.**
- From commercial: the abstention requirement, the provenance
  requirement, and the reviewer-in-the-loop UX.
- From research: the two-model verification pattern, the span-based
  extraction pattern, and the retrieval-based code lookup.

---

## Section 3 — UI/UX and wireframing

**Reference products.**
- **GitHub code review** — the accept/reject per item pattern, with a
  side-by-side view of the source and the diff.
- **Linear** — the density and speed of the command palette, the
  keyboard-first interaction.
- **Bloomberg terminal** — dense information with a lot happening at
  once, colour used semantically.
- **Notion / Obsidian** — the split-pane layout with a live document on
  one side and metadata on the other.

**Design decisions and justification.**

1. **Two-pane layout (note on the left, structured extraction on the
   right).** The coder's job is to compare the note against the
   extracted record. Putting both on screen at once is the fastest way
   to spot a mismatch. A single scrolling column would force back-and-
   forth scrolling.

2. **Accept/reject per item.** SOW 3.6 explicitly requires this. The
   interaction matches GitHub's review flow: per-item buttons that
   change state visibly. Reviewer decisions are stored in the session
   and reflected in the export.

3. **Colour-coded spans.** Green underline for accepted, amber for
   flagged. Colour is a fast signal at a distance. Hover links the
   highlight to the row and vice versa. Clicking a span scrolls the row
   into view.

4. **Trace viewer as a timeline, not a log.** A raw log is a wall of
   text. A timeline shows sequence, state, and progress at a glance.
   Each step is colour-coded (normal / warning / error) so the reviewer
   can see what happened without reading every line.

5. **Summary & recommendations card.** Shows the current state in one
   glance, offers actionable next steps (specific findings first, then
   generic tips), and displays the LLM-generated lifestyle
   recommendations under a clearly-labelled, disclaimed heading.

6. **Redis cache indicator in the top bar.** A visible pill shows the
   session's cache hit rate. This is a design decision, not just a
   metric: it tells the reviewer that re-runs are cheap, which
   encourages them to re-run notes whose extraction looks off.

7. **Deep teal accent, warm off-white background.** Deliberately not
   the default SaaS blue. The colour reads as clinical without being
   cold. The accent is reserved for actions (Run, Export) and the
   brand mark, so it does not compete with the semantic green / amber /
   red used for state.

**Wireframes.** [Insert screenshots of: empty state, loaded note, flagged
items, escalated note, trace viewer, AI recommendations section.]

---

## Section 4 — Execution

**Architecture diagram.** [Insert ARCHITECTURE.md diagram.]

**Pipeline walk-through of one note.**
1. **Section** — `src/sectioner.py` detects headings with regex. Offsets
   preserved.
2. **Mask** — `src/masker.py` masks names, dates, and identifiers with
   same-length fillers so spans still align. Regex for structured
   patterns; spaCy for names. Local only, no external API.
3. **Extract** — `src/extractor.py` calls Qwen 3.8 27B on Groq with a
   structured-output prompt. The model returns JSON with verbatim
   quotes, not offsets. Code resolves quotes to spans.
4. **ICD lookup** — `src/icd_index.py` runs BM25 and ChromaDB vector
   search over 74,260 ICD-10 codes, fuses them with RRF, applies a
   token-overlap confidence gate, and returns top-3 candidates or
   `NO_CONFIDENT_MATCH`.
5. **Verify** — `src/verifier.py` calls Gemini 3.5 Flash Lite with the
   masked note and the extracted items. The verifier does not see the
   extractor's prompt or reasoning. It returns verdicts, contradictions,
   and missed items.
6. **Reconcile** — `src/orchestrator.py` accepts items both passes agree
   on, flags disagreements, and escalates the note if the flagged
   fraction exceeds 40%.

**Extractor design.**
- **Why Qwen 3.8 27B on Groq** — free tier, fast enough, structured
  output supported. Temperature 0 for determinism.
- **Why not GPT-4 / Claude** — no paid tier available per SOW 4.1.
- **Why a quote-based span strategy** — the LLM is unreliable at
  counting characters. Returning the quote and letting code locate it
  is deterministic and auditable.

**Verifier design.**
- **Why a different model** — independence. If the verifier were the
  same model, it would inherit the same blind spots.
- **Why Gemini 3.5 Flash Lite** — stable, free tier, Google family
  (independent from Qwen).
- **Why fail-closed** — if the verifier is unavailable, items are
  marked REJECTED and flagged. The system never accepts an item it
  cannot verify.

**ICD index design.**
- **Why hybrid (BM25 + vector + RRF)** — BM25 catches exact terms;
  vector search catches paraphrases. RRF balances the two.
- **Why a token-overlap confidence gate** — a cosine threshold alone
  does not discriminate. We measured cosines between 0.85 and 0.89 for
  every query, common or rare. The gate checks whether the query's
  meaningful tokens appear in the top candidate's cleaned description.

**Orchestration.**
- Agent loop, not a fixed pipeline. Each step is a tool call that can
  fail or abstain.
- Reconciliation with bounded retries.
- Escalation when flagged fraction > 0.4.
- Full trace per note, viewable in the UI.

---

## Section 5 — Current limitations

- **Diagnoses F1 = 0.641** on the 78-note evaluated subset. Target is
  0.80. Recall-dominated; 113 missed gold diagnoses.
- **Medications F1 = 0.724** on the same subset. Target is 0.85.
  Precision is now strong (0.820); recall is the constraint.
- **Procedures precision = 0.577.** Over-specified procedure names and
  residual lab-test contamination.
- **Vitals F1 = 0.378.** Span convention mismatch between gold and
  extractor; the matcher bridges most of it.
- **Verifier net effect on F1 is small** and slightly negative on
  medications. Value is at the item level (correct rejections).
- **Groq free-tier rate limits** constrained the headline run to 78 of
  100 notes. Documented as Failure 8.
- **ICD confidence gate over-abstains** on a subset of common
  diagnoses. Documented as Failure 7.
- **Source data duplicate:** note_024 and note_041 are verbatim
  identical.
- **Gold labelling is LLM-assisted.** A hand spot-check of 15 notes is
  planned but not completed.

---

## Section 6 — Future scope

1. **Section-by-section extraction.** Highest-leverage change. Would
   address the diagnosed recall failure on both diagnoses and
   medications.
2. **Biomedical embedding model for the ICD index.** Replace
   `bge-small-en` with a clinical model (e.g. PubMedBERT embeddings) to
   restore separation between rare and common diagnoses.
3. **Feedback loop from reviewer decisions.** Accept/reject decisions
   could feed a fine-tuning or prompt-tuning loop.
4. **ICD hierarchical matching.** Chapter → category → code path with
   confidence at each level.
5. **Second verifier pass for ambiguous items.** The current verifier
   is a single call. A second pass with a different prompt would
   resolve disagreements.
6. **Full 100-note evaluation.** Complete the 22 skipped notes once the
   Groq daily cap resets, and re-run all eval scripts on the full set.
7. **Dedicated medications-extraction pass.** A medications-only
   prompt on the medication section of long notes.

---

**Rehearsal checklist.**
- Every design decision above has a one-sentence justification ready.
- Every metric quoted has a number and a source (eval report section).
- The live scenario is rehearsed against the reviewer UI, not the CLI.
- The trace viewer is shown as proof of the agent loop, not just as a log.
- The Redis cache is demonstrated by running one note twice and showing
  the hit-rate indicator change.