# Reviewer Interface — User Guide

**Project:** Clinical Note Extraction & ICD-10 Coding Agent (MVP)
**Audience:** Clinical coders and reviewers using the reviewer interface.
**Scope:** This guide covers the reviewer interface only. For installation and setup, see `README.md`.

---

## 1. What the interface does

The reviewer interface shows one clinical note at a time, alongside:

- the diagnoses, medications, procedures, allergies, and vitals the
  system extracted from the note
- the exact span of source text that supports each extracted item
- the ICD-10 candidate codes for each diagnosis
- the reason the verifier accepted or rejected each item
- a step-by-step trace of what the agent did

Every accepted item carries a span — a range of characters in the
original note — that supports it. Items the system cannot support are
flagged for human review rather than dropped silently.

---

## 2. Starting the interface

From the project root:

    uvicorn src.ui.app:app --reload --port 8000

Then open a browser to:

    http://localhost:8000

The note list in the left sidebar populates within a few seconds.
If it stays empty, see Section 8 (Troubleshooting).

---

## 3. The main screen

The interface has four panels:

**Left sidebar — Notes.** A list of every clinical note available for
review. A green dot next to a note indicates it has been run at least
once during this session. Click a note to select it.

**Top bar.** The currently selected note, a status indicator, a theme
toggle, and two buttons: **Export JSON** and **Run pipeline**.

**Left pane — Note.** The original note text. Spans supported by the
system are highlighted:

- Green underline and green background: accepted item.
- Amber underline and amber background: flagged item.

Hover over a highlighted span to highlight the corresponding row in the
right pane. Click a span to scroll the right pane to that item.

**Right pane — Results.** Three cards stacked vertically:

- **Accepted items** — one row per accepted item. Columns: item ID,
  type badge, item text (with ICD candidates for diagnoses), verifier
  reason, and Accept/Reject buttons.
- **Flagged items** — items the verifier rejected, or items with a
  status mismatch or missing verdict, with the reason for the flag.
- **Agent trace** — the step-by-step decision log for the current note.

---

## 4. Running the pipeline on a note

1. Click a note in the left sidebar.
2. Click **Run pipeline** in the top right.
3. The status indicator shows "Running note_XXX…".
4. When the run completes, the note appears in the left pane with
   highlighted spans, and the three result cards populate.

The first run of a note may take 10–60 seconds if the note is not
cached. Subsequent runs of the same note complete in under a second
because the extraction and verification responses are cached on disk.

---

## 5. Accepting and rejecting items

Every accepted item has two buttons in the rightmost column:

- **✓ (Accept)** — mark the item as correct. The button turns green.
- **✗ (Reject)** — mark the item as incorrect. The button turns red.

Decisions are stored in memory for the current session and included in
the JSON export. They are not persisted across server restarts.

Flagged items do not have Accept/Reject buttons — they need to be
resolved by editing the extraction or reviewing the note manually
before export.

---

## 6. Understanding the trace

The Agent trace card shows every step the pipeline took for the current
note. Each line is numbered and color-coded:

- **Blue dot** — a normal step (sectioning, extraction, reconciliation).
- **Amber dot** — a flagged item, a contradiction, or a missed item
  reported by the verifier.
- **Red dot** — an escalation, a verifier failure, or an error.

Typical trace:

    00  sectioned into 5 section(s)
    01  masked 0 PII item(s); length preserved=True
    02  extracted 11 item(s)
    03  extract took 3.42s
    04  verifier: 11 accepted, 0 flagged
    05  verify took 1.87s
    06  missed items reported: 1
    07  missed [diagnosis]: headaches

---

## 7. Exporting the accepted record

Click **Export JSON** in the top bar. The browser downloads a file named
`<note_id>_accepted.json` containing:

- the note ID
- whether the note was escalated
- every accepted item, with its span, verifier reason, and ICD
  candidates
- every flagged item with its reason
- the reviewer's decisions (accepted/rejected) if any were made

The JSON is the hand-off artifact for downstream systems. It is not
written to disk by the server; the browser handles the download.

---

## 8. Troubleshooting

**The note list is empty.**
The server may not be running, or the browser is pointed at the wrong
URL. Confirm `http://localhost:8000` and check the uvicorn terminal for
errors.

**"Running note_XXX…" never completes.**
The extractor or verifier may be rate-limited by the upstream API (Groq
or Google). Wait 30–60 seconds; the pipeline retries automatically. If it
still does not complete, check the uvicorn terminal for the traceback.

**Highlighted spans look misaligned.**
Spans are character offsets into the original (unmasked) note text. If
the alignment is off, open an issue; this usually indicates a masking bug
where the masked text length differs from the original.

**I want to reset my accept/reject decisions.**
Restart the server. Decisions are stored in memory and cleared on
restart.

---

## 9. What the interface does not do

- It does not edit the note text.
- It does not write the accepted record to the database; use the JSON
  export.
- It does not support multiple concurrent reviewers. One server, one
  reviewer session at a time (per SOW Section 7.2).
- It does not apply ICD coding to procedures (out of scope for the MVP).


## Colour coding — what each colour means

### Note highlighting

- **Green background and underline** — accepted item. The extractor and
  verifier agree that the span supports the item.
- **Amber background and underline** — flagged item. The verifier rejected
  it, the status was wrong, or the extractor-verifier pair disagreed.
- **Hover** any highlighted span to highlight the matching row in the
  results pane. Click a span to scroll the row into view.

### Flagged-item reason chips

Each flagged item carries a colour-coded chip above the reason text:

- **Contradiction (red)** — the note contradicts itself. The verifier
  found two statements that cannot both be true.
- **Status mismatch (amber)** — the note contradicts the status the
  extractor assigned to the item (e.g. it labelled a medication
  "current" when the note says it was discontinued).
- **Verifier rejected (amber)** — the verifier found no support for the
  item in the note, or the item is the wrong category.
- **No verdict (grey)** — the verifier did not return a verdict for this
  item. Typically a parsing failure on the verifier response.
- **Verifier unavailable (red)** — the verifier API failed. All items in
  that run are marked "unavailable" and the note is escalated.

Each flagged item also shows a suggested action below the reason
(e.g. "Review the status. The note contradicts the extractor's label.").

### Diagnosis status chips

- **active (blue)** — the condition is currently present or being treated.
- **historical (grey)** — the condition is in the past, resolved, or not
  current.
- **ruled_out (red)** — the note explicitly says the patient does NOT have
  it.
- **suspected (amber)** — the note says maybe/possibly ("rule out X",
  "concern for X").

### Escalation banner

If the flagged fraction for a note exceeds 40%, a red banner appears at
the top of the screen and the note is marked escalated. This means the
system found a lot of disagreement and the whole note should be reviewed
manually rather than trusting the accepted items.

---