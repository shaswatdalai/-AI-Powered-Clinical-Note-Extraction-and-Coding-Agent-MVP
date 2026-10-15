"""
Reviewer interface backend (SOW 3.6 / 6.2).

Serves two static pages:
- /          -> landing.html (entry page)
- /reviewer  -> reviewer.html (the working reviewer UI)
- /static/*  -> any other static asset

Endpoints:
- GET  /api/notes
- GET  /api/notes/{id}
- POST /api/notes/{id}/run
- GET  /api/cache/stats
- POST /api/cache/reset
- POST /api/decide/{item_id}
- GET  /api/decisions
- POST /api/notes/{id}/export
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
    # Recall-check findings (verifier-promoted). Either accept them as
    # genuine additions to the record, or dismiss them as false positives.
    "verifier recall check": "The verifier found this in the note but the extractor missed it. Accept if genuine, otherwise dismiss.",
    "missed by extractor": "The verifier found this in the note but the extractor missed it. Accept if genuine, otherwise dismiss.",
    "verifier found this in the note": "The verifier found this in the note but the extractor missed it. Accept if genuine, otherwise dismiss.",
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


def _generate_advice(result: dict) -> dict:
    """Sidecar: call the advisor with the note's accepted diagnoses.

    Always returns a dict of the shape:
        {"advice": [...], "reason": "ok" | "no_diagnoses" | "empty_tips"
                                    | "unavailable" | "error", "message": str}
    """
    diag_names = [
        (it.get("text") or "")
        for it in result.get("accepted", [])
        if it.get("type") == "diagnosis"
    ]
    diag_names = [d for d in diag_names if d and d.strip()]

    if not diag_names:
        return {
            "advice": [],
            "reason": "no_diagnoses",
            "message": "No diagnoses were accepted for this note.",
        }

    try:
        out = advisor.generate(diag_names)
    except Exception as e:
        return {
            "advice": [],
            "reason": "error",
            "message": f"{type(e).__name__}: {str(e)[:120]}",
        }

    if out is None:
        return {
            "advice": [],
            "reason": "unavailable",
            "message": "Advisor returned no usable advice.",
        }

    advice_list = out.get("advice") or []
    if not advice_list:
        return {
            "advice": [],
            "reason": "empty_tips",
            "message": "The model returned no actionable tips for these diagnoses.",
        }

    return {
        "advice": advice_list,
        "disclaimer": out.get("disclaimer"),
        "reason": "ok",
    }


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

    cached = redis_cache.get_result(note_id, note_text)
    if cached is not None:
        cached["cache_source"] = "redis"
        cached["summary"] = _summarize_pipeline_result(cached, note_id)
        cached["flagged"] = _annotate_flagged(cached.get("flagged", []))
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

    to_store = dict(response)
    to_store.pop("cache_source", None)
    to_store.pop("advice", None)
    redis_cache.set_result(note_id, note_text, to_store)

    return response


# ---------------------------------------------------------------------------
# Cache stats
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
def landing():
    return FileResponse(STATIC_DIR / "landing.html")


@app.get("/reviewer")
def reviewer():
    return FileResponse(STATIC_DIR / "reviewer.html")


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")