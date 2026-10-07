"""
Extractor: calls the extractor LLM (Qwen 3.8 27B via Groq) and parses
the response into a validated Extraction object with resolved spans.

Design rules:
- The LLM receives ONE masked note + instructions. Nothing else.
- The LLM returns JSON with verbatim quotes, NOT offsets. Code computes
  offsets from the quotes.
- If the LLM returns invalid JSON, retry up to 2 times.
- Cache every response on disk keyed by hash(model + prompt + schema).
"""

import hashlib
import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

from src.schema import (
    Diagnosis,
    Evidence,
    Extraction,
    Medication,
    Procedure,
    Allergy,
    Vital,
    Span,
)


load_dotenv()

PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT = (PROMPTS_DIR / "extractor_system.txt").read_text(encoding="utf-8")
USER_PROMPT_TEMPLATE = (PROMPTS_DIR / "extractor_user.txt").read_text(encoding="utf-8")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "qwen-3.8-27b"
MAX_RETRIES = 2
CACHE_DIR = Path("cache") / "extractor"


def _cache_key(note_text: str) -> str:
    """Hash the (model, prompt, note) tuple for cache lookup."""
    payload = f"{GROQ_MODEL}|{SYSTEM_PROMPT}|{note_text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_cache(key: str) -> dict | None:
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _write_cache(key: str, value: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / f"{key}.json").write_text(
        json.dumps(value, indent=2), encoding="utf-8"
    )


def _call_groq(note_text: str) -> dict:
    """Call the Groq API and return the parsed JSON body."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    user_prompt = USER_PROMPT_TEMPLATE.format(note_text=note_text)

    response = httpx.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        },
        timeout=60.0,
    )
    response.raise_for_status()
    body = response.json()
    return json.loads(body["choices"][0]["message"]["content"])


def _resolve_span(note_text: str, quote: str) -> Span | None:
    """
    Find the quote in the note and return its span.
    Returns None if the quote can't be located.
    Uses exact match, then whitespace-normalised match.
    """
    if not quote:
        return None

    # Exact match
    start = note_text.find(quote)
    if start != -1:
        return Span(start=start, end=start + len(quote))

    # Whitespace-normalised match: collapse runs of whitespace
    import re
    normalised_quote = re.sub(r"\s+", " ", quote).strip()
    normalised_note = re.sub(r"\s+", " ", note_text)

    norm_start = normalised_note.find(normalised_quote)
    if norm_start == -1:
        return None

    # Map the normalised offset back to the original offset.
    # Walk through the original text, counting normalised positions.
    orig_pos = 0
    norm_pos = 0
    while norm_pos < norm_start and orig_pos < len(note_text):
        if note_text[orig_pos].isspace():
            while orig_pos < len(note_text) and note_text[orig_pos].isspace():
                orig_pos += 1
            norm_pos += 1
        else:
            orig_pos += 1
            norm_pos += 1

    # orig_pos is now at the start of the match in the original text
    span_start = orig_pos
    span_end = span_start + len(normalised_quote)
    # Trim trailing to fit actual text
    while span_end > span_start and note_text[span_end - 1].isspace():
        span_end -= 1
    return Span(start=span_start, end=span_end)


def _build_extraction(raw: dict, note_text: str) -> Extraction:
    """Convert the raw LLM JSON into a validated Extraction with spans."""
    diagnoses = []
    for d in raw.get("diagnoses", []):
        quote = d.get("evidence_quote", "")
        span = _resolve_span(note_text, quote)
        diagnoses.append(Diagnosis(
            name_as_written=d.get("name_as_written", ""),
            normalised_name=d.get("normalised_name", d.get("name_as_written", "")),
            status=d.get("status", "active"),
            evidence=Evidence(quote=quote, span=span),
        ))

    medications = []
    for m in raw.get("medications", []):
        quote = m.get("evidence_quote", "")
        span = _resolve_span(note_text, quote)
        medications.append(Medication(
            name=m.get("name", ""),
            dose=m.get("dose"),
            route=m.get("route"),
            frequency=m.get("frequency"),
            status=m.get("status", "current"),
            evidence=Evidence(quote=quote, span=span),
        ))

    procedures = []
    for p in raw.get("procedures", []):
        quote = p.get("evidence_quote", "")
        span = _resolve_span(note_text, quote)
        procedures.append(Procedure(
            name=p.get("name", ""),
            date=p.get("date"),
            evidence=Evidence(quote=quote, span=span),
        ))

    allergies = []
    for a in raw.get("allergies", []):
        quote = a.get("evidence_quote", "")
        span = _resolve_span(note_text, quote)
        allergies.append(Allergy(
            substance=a.get("substance", ""),
            reaction=a.get("reaction"),
            evidence=Evidence(quote=quote, span=span),
        ))

    vitals = []
    for v in raw.get("vitals", []):
        quote = v.get("evidence_quote", "")
        span = _resolve_span(note_text, quote)
        vitals.append(Vital(
            name=v.get("name", ""),
            value=v.get("value", ""),
            unit=v.get("unit"),
            evidence=Evidence(quote=quote, span=span),
        ))

    return Extraction(
        diagnoses=diagnoses,
        medications=medications,
        procedures=procedures,
        allergies=allergies,
        vitals=vitals,
    )


def extract(note_text: str) -> Extraction:
    """
    Extract items from a note.

    Calls the LLM (or reads from cache), validates the JSON, and
    resolves quotes to character offsets.
    """
    key = _cache_key(note_text)
    cached = _read_cache(key)

    if cached is None:
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                raw = _call_groq(note_text)
                cached = raw
                _write_cache(key, cached)
                break
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    time.sleep(2 ** attempt)
        if cached is None:
            raise RuntimeError(f"Extractor failed after {MAX_RETRIES + 1} attempts: {last_error}")

    return _build_extraction(cached, note_text)