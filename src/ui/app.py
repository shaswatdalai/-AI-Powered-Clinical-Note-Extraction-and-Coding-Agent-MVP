"""
Reviewer interface backend (SOW 3.6 / 6.2).

Serves a single-page app that renders one clinical note at a time with:
- the note text, with accepted and flagged item spans highlighted
- a structured table of accepted items (diagnoses with ICD candidates,
  medications, procedures, allergies, vitals)
- a flagged-items panel with the reason for each flag
- an agent trace viewer for the current note
- JSON export of the accepted record

Design:
- FastAPI, one process, localhost only.
- Reads notes from data/note_*.txt.
- Calls src.orchestrator.run(note_text) per note. The orchestrator uses
  the extractor and verifier caches, so runs are fast after the first.
- Reviewer accept/reject decisions are stored in memory for the session.
  Not persisted; restarting the server resets them. This is intentional
  for the MVP demo (SOW 7.2: simple UI, single reviewer session).
"""

import json
from src.icd_index import load_index
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.orchestrator import run


DATA_DIR = Path("data")
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Clinical Extraction Reviewer")
@app.on_event("startup")
def _startup():
    """Load the ICD index once when the server starts.

    The orchestrator calls icd_lookup for each diagnosis. icd_lookup
    asserts that the BM25 and ChromaDB indexes are loaded; without this
    the pipeline crashes with an AssertionError.
    """
    load_index()

# ---------------------------------------------------------------------------
# In-memory reviewer decisions. Keyed by item id. Value: "accepted" | "rejected".
# Reset when the server restarts.
# ---------------------------------------------------------------------------
_reviewer_decisions: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Note listing and retrieval
# ---------------------------------------------------------------------------

def _list_note_ids() -> list[str]:
    files = sorted(DATA_DIR.glob("note_*.txt"))
    return [f.stem for f in files]


@app.get("/api/notes")
def list_notes():
    return {"notes": _list_note_ids()}


@app.get("/api/notes/{note_id}")
def get_note(note_id: str):
    path = DATA_DIR / f"{note_id}.txt"
    if not path.exists():
        raise HTTPException(404, f"note {note_id!r} not found")
    return {"note_id": note_id, "text": path.read_text(encoding="utf-8")}


# ---------------------------------------------------------------------------
# Run the pipeline on one note.
# Uses the orchestrator, which uses the extractor and verifier caches.
# Safe to call repeatedly on the same note.
# ---------------------------------------------------------------------------

@app.post("/api/notes/{note_id}/run")
def run_note(note_id: str):
    path = DATA_DIR / f"{note_id}.txt"
    if not path.exists():
        raise HTTPException(404, f"note {note_id!r} not found")

    note_text = path.read_text(encoding="utf-8")
    try:
        result = run(note_text)
    except Exception as e:
        raise HTTPException(500, f"pipeline failed: {type(e).__name__}: {e}")

    return {
        "note_id": note_id,
        "note_text": note_text,
        "accepted": result["accepted"],
        "flagged": result["flagged"],
        "trace": result["trace"],
        "escalated": result["escalated"],
    }


# ---------------------------------------------------------------------------
# Reviewer decisions
# ---------------------------------------------------------------------------

@app.post("/api/decide/{item_id}")
def decide(item_id: str, decision: str):
    if decision not in ("accepted", "rejected", "clear"):
        raise HTTPException(400, "decision must be accepted | rejected | clear")
    if decision == "clear":
        _reviewer_decisions.pop(item_id, None)
    else:
        _reviewer_decisions[item_id] = decision
    return {"item_id": item_id, "decision": _reviewer_decisions.get(item_id)}


@app.get("/api/decisions")
def list_decisions():
    return {"decisions": dict(_reviewer_decisions)}


# ---------------------------------------------------------------------------
# JSON export
# ---------------------------------------------------------------------------

@app.post("/api/notes/{note_id}/export")
def export_note(note_id: str):
    path = DATA_DIR / f"{note_id}.txt"
    if not path.exists():
        raise HTTPException(404, f"note {note_id!r} not found")

    note_text = path.read_text(encoding="utf-8")
    result = run(note_text)

    def _annotate(item: dict) -> dict:
        item_id = item.get("id")
        d = dict(item)
        d["reviewer_decision"] = _reviewer_decisions.get(item_id)
        return d

    accepted = [_annotate(it) for it in result["accepted"]]
    flagged = [
        {
            "id": f.get("id"),
            "item": f.get("item"),
            "reason": f.get("reason"),
            "reviewer_decision": _reviewer_decisions.get(f.get("id")),
        }
        for f in result["flagged"]
    ]

    payload = {
        "note_id": note_id,
        "escalated": result["escalated"],
        "accepted": accepted,
        "flagged": flagged,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": f'attachment; filename="{note_id}_accepted.json"'
        },
    )


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")