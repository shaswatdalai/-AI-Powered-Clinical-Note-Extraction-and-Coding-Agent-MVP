"""
Extractor: calls the extractor LLM (Qwen 3.8 27B via Groq) and parses
the response into a validated Extraction object with resolved spans.

Design rules:
- The LLM receives ONE masked note + instructions. Nothing else.
- The LLM returns JSON with verbatim quotes, NOT offsets. Code computes
  offsets from the quotes.
- Status values are normalized before validation — LLMs sometimes emit
  synonyms ("taking", "active", "past") that must map to the enum.
- If a single item fails validation, it is dropped and the rest of the
  note is kept. A whole note never fails because one item was malformed.
- Cache every response on disk keyed by hash(model + prompt + note).
"""

import hashlib
import json
import os
import re
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

from src.guardrails import wrap_note
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
GROQ_MODEL = "qwen/qwen3.8-27b"
MAX_RETRIES = 5
RATE_LIMIT_SLEEP = 30
CACHE_DIR = Path("cache") / "extractor"


# Allowed enum values (must match src/schema.py)
DIAG_STATUSES = {"active", "historical", "ruled_out", "suspected"}
MED_STATUSES = {"current", "discontinued", "newly_prescribed"}

# Status synonyms the LLM might emit. Keys are normalized (lowercase,
# underscores). Values must be in the allowed sets above.
STATUS_SYNONYMS = {
    # Medication synonyms
    "active": "current",
    "taking": "current",
    "ongoing": "current",
    "prescribed": "newly_prescribed",
    "started": "newly_prescribed",
    "new": "newly_prescribed",
    "past": "discontinued",
    "stopped": "discontinued",
    "ended": "discontinued",
    "not_current": "discontinued",
    # Diagnosis synonyms
    "current": "active",
    "present": "active",
    "past_history": "historical",
    "resolved": "historical",
    "history": "historical",
    "negated": "ruled_out",
    "denied": "ruled_out",
    "no": "ruled_out",
    "possible": "suspected",
    "probable": "suspected",
    "rule_out": "suspected",
    "working": "suspected",
}


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

    wrapped = wrap_note(note_text)
    user_prompt = USER_PROMPT_TEMPLATE.format(note_text=wrapped)

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

    if response.status_code == 429:
        retry_after = response.headers.get("retry-after", "30")
        raise RuntimeError(f"429 rate limited; retry-after={retry_after}")

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
    normalised_quote = re.sub(r"\s+", " ", quote).strip()
    normalised_note = re.sub(r"\s+", " ", note_text)

    norm_start = normalised_note.find(normalised_quote)
    if norm_start == -1:
        return None

    # Map the normalised offset back to the original offset.
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

    span_start = orig_pos
    span_end = span_start + len(normalised_quote)
    while span_end > span_start and note_text[span_end - 1].isspace():
        span_end -= 1
    return Span(start=span_start, end=span_end)


def _normalize_status(raw_status: str, allowed: set[str], fallback: str) -> str:
    """Normalize an LLM-returned status to one of the allowed enum values."""
    if not raw_status or not isinstance(raw_status, str):
        return fallback
    s = raw_status.strip().lower().replace(" ", "_").replace("-", "_")
    if s in allowed:
        return s
    mapped = STATUS_SYNONYMS.get(s)
    if mapped and mapped in allowed:
        return mapped
    return fallback


def _safe_build(model_class, **kwargs):
    """Try to construct a model. On validation error, return None."""
    try:
        return model_class(**kwargs)
    except Exception as e:
        # Log and drop the item
        print(f"  [drop] {model_class.__name__} failed validation: {str(e)[:120]}")
        return None


def _build_extraction(raw: dict, note_text: str) -> Extraction:
    """Convert the raw LLM JSON into a validated Extraction with spans.

    Span strategy: prefer the shorter, canonical name field
    (name_as_written for diagnoses, name for others). Fall back to the
    evidence quote only when the name can't be located.

    Status strategy: normalize synonyms to enum values.

    Error strategy: if one item fails validation, drop it and keep the
    rest. The whole note does not fail because of a single bad item.
    """
    def resolve(name: str, quote: str) -> Span | None:
        s = _resolve_span(note_text, name) if name else None
        if s is None and quote:
            s = _resolve_span(note_text, quote)
        return s

    diagnoses = []
    for d in raw.get("diagnoses", []):
        name = d.get("name_as_written", "")
        quote = d.get("evidence_quote", "")
        status = _normalize_status(d.get("status", ""), DIAG_STATUSES, "active")
        item = _safe_build(
            Diagnosis,
            name_as_written=name,
            normalised_name=d.get("normalised_name", name),
            status=status,
            evidence=Evidence(quote=quote, span=resolve(name, quote)),
        )
        if item:
            diagnoses.append(item)

    medications = []
    for m in raw.get("medications", []):
        name = m.get("name", "")
        quote = m.get("evidence_quote", "")
        status = _normalize_status(m.get("status", ""), MED_STATUSES, "current")
        item = _safe_build(
            Medication,
            name=name,
            dose=m.get("dose"),
            route=m.get("route"),
            frequency=m.get("frequency"),
            status=status,
            evidence=Evidence(quote=quote, span=resolve(name, quote)),
        )
        if item:
            medications.append(item)

    procedures = []
    for p in raw.get("procedures", []):
        name = p.get("name", "")
        quote = p.get("evidence_quote", "")
        item = _safe_build(
            Procedure,
            name=name,
            date=p.get("date"),
            evidence=Evidence(quote=quote, span=resolve(name, quote)),
        )
        if item:
            procedures.append(item)

    allergies = []
    for a in raw.get("allergies", []):
        name = a.get("substance", "")
        quote = a.get("evidence_quote", "")
        item = _safe_build(
            Allergy,
            substance=name,
            reaction=a.get("reaction"),
            evidence=Evidence(quote=quote, span=resolve(name, quote)),
        )
        if item:
            allergies.append(item)

    vitals = []
    for v in raw.get("vitals", []):
        name = v.get("name", "")
        quote = v.get("evidence_quote", "")
        item = _safe_build(
            Vital,
            name=name,
            value=v.get("value", ""),
            unit=v.get("unit"),
            evidence=Evidence(quote=quote, span=resolve(name, quote)),
        )
        if item:
            vitals.append(item)

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
                is_rate_limit = "429" in str(e) or "rate" in str(e).lower()
                if attempt < MAX_RETRIES:
                    sleep_for = RATE_LIMIT_SLEEP if is_rate_limit else (2 ** attempt)
                    print(f"  [retry] attempt {attempt + 1}/{MAX_RETRIES}; sleeping {sleep_for}s")
                    time.sleep(sleep_for)
        if cached is None:
            raise RuntimeError(f"Extractor failed after {MAX_RETRIES + 1} attempts: {last_error}")

    return _build_extraction(cached, note_text)