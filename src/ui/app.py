"""
Reviewer interface backend (SOW 3.6 / 6.2).

Serves a single-page app that renders one clinical note at a time with:
- the note text, with accepted and flagged item spans highlighted
- a summary line and per-note item counts
- a structured table of accepted items (diagnoses with ICD candidates,
  medications, procedures, allergies, vitals)
- a flagged-items panel with a reason and a suggested action per item
- an agent trace viewer for the current note
- JSON export of the accepted record

Design and reviewer feedback integration:

- FastAPI, one process, localhost only. Runs single-worker by default
  because SOW 7.2 assumes a single reviewer session. For multi-reviewer
  use, run: `uvicorn src.ui.app:app --workers N`. Each worker loads its
  own copy of the ICD index (~250 MB), so N=2 is the practical ceiling
  on a laptop.

- Prompt caching, three layers:
  (a) Redis cache for whole-note results, keyed by
      sha256(note_id | prompt_hash | note_text). Re-running the same
      note is instant. Editing any prompt invalidates the cache
      automatically. Falls back cleanly if Redis is down.
  (b) On-disk LLM-response cache in cache/extractor and cache/verifier,
      keyed by model + both prompts + guardrails/schema fingerprint +
      input. This is what makes fresh extractions cheap after the first
      run of each note.
  (c) Redis cache for the advisor module's per-condition lifestyle tips,
      keyed by the sorted list of diagnosis names.

- Reads notes from data/note_*.txt.
- Calls src.orchestrator.run(note_text) per note.
- Reviewer accept/reject decisions are stored in memory for the session.
  Not persisted; restarting the server resets them. Intentional for the
  MVP demo (SOW 7.2: single reviewer session).
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.advice import advisor
from src.cache import redis_cache
from src.icd_index import load_index
from src.orchestrator import run


DATA_DIR = Path("data")
STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Clinical Extraction Reviewer")


@app.on_event("startup")
def _startup():
    """Load the ICD index once at startup. Redis is optional."""
    load_index()


_reviewer_decisions: dict[str, str] = {}


# ---------------------------------------------------------------------------
# Summary and suggested-action helpers
# ---------------------------------------------------------------------------

_SUGGESTIONS: dict[str, str] = {
    "status mismatch": "Review the status. The note contradicts the extractor's label.",
    "verifier rejected": "Consider removing this item — the verifier found no support.",
    "no verdict returned by verifier": "Re-run the pipeline, or review manually.",
    "verifier unavailable": "Retry the run; the verifier did not respond.",
    "contradiction": "The note contradicts itself. Confirm which statement is correct.",
    "icd": "No confident ICD-10 match. Review the coding manually.",
}


def _suggest_action(reason: str) -> str:
    if not reason:
        return "Review manually."
    r = reason.lower()
    for key, suggestion in _SUGGESTIONS.items():
        if key in r:
            return suggestion
    return "Review manually."


def _summarize_pipeline_result(result: dict, note_id: str) -> str:
    accepted = result.get("accepted", [])
    flagged = result.get("flagged", [])
    escalated = result.get("escalated", False)
    error = result.get("error")
    counts: dict[str, int] = {}
    for item in accepted:
        t = item.get("type") or "item"
        counts[t] = counts.get(t, 0) + 1
    order = ["diagnosis", "medication", "procedure", "allergy", "vital"]
    parts = []
    for t in order:
        n = counts.get(t, 0)
        if n:
            parts.append(f"{n} {t}{'' if n == 1 else 's'}")
    for t, n in counts.items():
        if t not in order:
            parts.append(f"{n} {t}{'' if n == 1 else 's'}")
    body = ", ".join(parts) if parts else "no items"
    tail = f" · {len(flagged)} flagged" if flagged else ""
    esc = " · ESCALATED" if escalated else ""
    err = f" · ERROR: {error[:60]}" if error else ""
    return f"{note_id}: {body}{tail}{esc}{err}."


def _annotate_flagged(flagged: list[dict]) -> list[dict]:
    out = []
    for f in flagged:
        item = dict(f)
        item["suggested_action"] = _suggest_action(f.get("reason", ""))
        out.append(item)
    return out


def _generate_advice(result: dict) -> dict | None:
    """Sidecar: call the advisor with the note's accepted diagnoses.

    Fails silently if the advisor module or the LLM is unavailable —
    the review interface still works.
    """
    try:
        diag_names = [
            (it.get("text") or "")
            for it in result.get("accepted", [])
            if it.get("type") == "diagnosis"
        ]
        return advisor.generate(diag_names)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Notes
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
# Run pipeline with Redis result cache
# ---------------------------------------------------------------------------

@app.post("/api/notes/{note_id}/run")
def run_note(note_id: str):
    path = DATA_DIR / f"{note_id}.txt"
    if not path.exists():
        raise HTTPException(404, f"note {note_id!r} not found")

    note_text = path.read_text(encoding="utf-8")

    # Redis cache check for the whole pipeline result
    cached = redis_cache.get_result(note_id, note_text)
    if cached is not None:
        cached["cache_source"] = "redis"
        cached["summary"] = _summarize_pipeline_result(cached, note_id)
        cached["flagged"] = _annotate_flagged(cached.get("flagged", []))
        # Advice is cheap if it is also cached — just call it.
        cached["advice"] = _generate_advice(cached)
        return cached

    try:
        result = run(note_text)
    except Exception as e:
        raise HTTPException(500, f"pipeline failed: {type(e).__name__}: {e}")

    flagged = _annotate_flagged(result["flagged"])
    advice = _generate_advice(result)

    response = {
        "note_id": note_id,
        "note_text": note_text,
        "summary": _summarize_pipeline_result(result, note_id),
        "accepted": result["accepted"],
        "flagged": flagged,
        "trace": result["trace"],
        "escalated": result["escalated"],
        "error": result.get("error"),
        "advice": advice,
        "cache_source": "fresh",
    }

    # Store in Redis (no-op if Redis is down). Advice is cached separately
    # by the advisor module, so we don't persist it here.
    to_store = dict(response)
    to_store.pop("cache_source", None)
    to_store.pop("advice", None)
    redis_cache.set_result(note_id, note_text, to_store)

    return response


# ---------------------------------------------------------------------------
# Cache stats (for the UI banner)
# ---------------------------------------------------------------------------

@app.get("/api/cache/stats")
def cache_stats():
    return redis_cache.stats()


@app.post("/api/cache/reset")
def cache_reset():
    redis_cache.flush()
    redis_cache.reset_stats()
    return {"ok": True}


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
# Export
# ---------------------------------------------------------------------------

@app.post("/api/notes/{note_id}/export")
def export_note(note_id: str):
    path = DATA_DIR / f"{note_id}.txt"
    if not path.exists():
        raise HTTPException(404, f"note {note_id!r} not found")

    note_text = path.read_text(encoding="utf-8")
    cached = redis_cache.get_result(note_id, note_text)
    result = cached if cached is not None else run(note_text)

    def _annotate(item: dict) -> dict:
        d = dict(item)
        d["reviewer_decision"] = _reviewer_decisions.get(d.get("id"))
        return d

    accepted = [_annotate(it) for it in result["accepted"]]
    flagged = [
        {
            "id": f.get("id"),
            "item": f.get("item"),
            "reason": f.get("reason"),
            "suggested_action": _suggest_action(f.get("reason", "")),
            "reviewer_decision": _reviewer_decisions.get(f.get("id")),
        }
        for f in result["flagged"]
    ]

    payload = {
        "note_id": note_id,
        "summary": _summarize_pipeline_result(result, note_id),
        "escalated": result["escalated"],
        "error": result.get("error"),
        "accepted": accepted,
        "flagged": flagged,
        "advice": _generate_advice(result),
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{note_id}_accepted.json"'},
    )


# ---------------------------------------------------------------------------
# Static frontend
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")