"""
Independent verifier: a second LLM pass that judges every item the
extractor produced.

Design rules:
- Verifier receives: masked note + list of items + ICD candidates.
- Verifier NEVER receives: the extractor's prompt, chain-of-thought, or
  confidence. That is what "independent" means here.
- If the verifier fails or returns invalid JSON, all items are marked
  UNVERIFIED and flagged. Fail closed.
- Every response is cached on disk keyed by hash(model + prompt + items).
"""

import hashlib
import json
import os
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

from src.guardrails import wrap_note
from src.schema import (
    VerifierResponse,
    Verdict,
    Contradiction,
    MissedItem,
)


load_dotenv()

PROMPTS_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT = (PROMPTS_DIR / "verifier_system.txt").read_text(encoding="utf-8")
USER_PROMPT_TEMPLATE = (PROMPTS_DIR / "verifier_user.txt").read_text(encoding="utf-8")

GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GOOGLE_MODEL = "gemini-3.8-flash"   # adjust to actual model name
MAX_RETRIES = 6
CACHE_DIR = Path("cache") / "verifier"


def _cache_key(note_masked: str, items_json: str) -> str:
    payload = f"{GOOGLE_MODEL}|{SYSTEM_PROMPT}|{note_masked}|{items_json}"
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


def _serialize_items(items: list[dict]) -> str:
    return json.dumps(items, indent=2, sort_keys=True)


def _call_gemini(note_masked: str, items_json: str) -> dict:
    """Call Gemini and return the parsed JSON."""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set")

    from src.guardrails import wrap_note
    wrapped_note = wrap_note(note_masked)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        note_masked=wrapped_note,
        items_json=items_json,
    )

    url = GOOGLE_API_URL.format(model=GOOGLE_MODEL)
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
    }

    response = httpx.post(
        url,
        params={"key": api_key},
        json=body,
        timeout=60.0,
    )

    if response.status_code == 429:
        raise RuntimeError(f"429 rate limited; retry-after={response.headers.get('retry-after', '30')}")

    response.raise_for_status()
    body = response.json()
    text = body["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def _empty_unverified_response(item_ids: list[str], reason: str) -> dict:
    """When the verifier fails, mark every item as UNVERIFIED."""
    return {
        "verdicts": [
            {"id": i, "verdict": "REJECTED", "status_correct": False,
             "icd_fit": None, "reason": f"verifier unavailable: {reason}"}
            for i in item_ids
        ],
        "contradictions": [],
        "missed_items": [],
    }


def verify(note_masked: str, items: list[dict]) -> VerifierResponse:
    """
    Verify each item against the masked note.

    items: list of dicts, each with at least {"id": str, ...}.
           The full item dict is passed to the verifier so it can judge
           status, ICD fit, etc.

    Returns a VerifierResponse. On failure, returns a response where all
    items are marked REJECTED with reason "verifier unavailable".
    """
    if not items:
        return VerifierResponse()

    items_json = _serialize_items(items)
    key = _cache_key(note_masked, items_json)
    cached = _read_cache(key)

    if cached is None:
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                cached = _call_gemini(note_masked, items_json)
                _write_cache(key, cached)
                break
            except Exception as e:
                last_error = e
                is_rate = "429" in str(e)
                is_503 = "503" in str(e) or "Service Unavailable" in str(e)
                if attempt < MAX_RETRIES:
                   if is_rate:
                        sleep_for = 30
                   elif is_503:
                        sleep_for = min(2 ** (attempt + 2), 60)   # 4, 8, 16, 32, 60, 60 seconds
                   else:
                        sleep_for = 2 ** attempt
                   print(f"  [verifier retry] attempt {attempt + 1}/{MAX_RETRIES}; sleeping {sleep_for}s")
                   time.sleep(sleep_for)
        if cached is None:
            # Fail closed: mark every item as unverified
            print(f"  [verifier] failed after {MAX_RETRIES + 1} attempts; marking all items unverified")
            cached = _empty_unverified_response(
                [item.get("id", "?") for item in items],
                str(last_error)[:100],
            )

    # Parse into the schema
    try:
        return VerifierResponse(
            verdicts=[Verdict(**v) for v in cached.get("verdicts", [])],
            contradictions=[Contradiction(**c) for c in cached.get("contradictions", [])],
            missed_items=[MissedItem(**m) for m in cached.get("missed_items", [])],
        )
    except Exception as e:
        print(f"  [verifier] malformed response: {e}")
        return VerifierResponse(
            verdicts=[
                Verdict(id=item.get("id", "?"), verdict="REJECTED",
                        status_correct=False, icd_fit=None,
                        reason=f"malformed verifier response: {e}")
                for item in items
            ],
        )