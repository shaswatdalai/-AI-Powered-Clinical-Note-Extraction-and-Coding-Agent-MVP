"""
Lifestyle and prevention advisor (sidecar, not part of the extraction pipeline).

Takes the accepted diagnoses from a pipeline run and asks Gemini 3.5 Flash
Lite for general lifestyle, monitoring, and preventive guidance. The
response is cached in Redis keyed by the sorted list of diagnoses.

Design rules:
- This module NEVER touches extracted items, spans, or verification. It is
  a presentation-layer sidecar.
- The prompt explicitly forbids: dosages, drug names, treatment plans,
  diagnosis changes, and anything that reads as clinical advice for a
  specific patient. Only generic lifestyle and preventive guidance.
- Output is labelled in the UI as "Our recommendations" with a disclaimer
  that it is NOT extracted from the note.
- If the LLM call fails, the module returns None and the UI shows the
  unavailable state. The review still works.

Rate limiting:
- Gemini's free tier limits requests per minute. When the UI runs several
  notes back-to-back, every advisor call after the first hits 429 unless
  we space them out. A module-level lock serialises calls and enforces a
  minimum interval between them.
"""

import hashlib
import json
import os
import threading
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv


load_dotenv()

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_ADVICE_PROMPT_PATH = PROMPTS_DIR / "advisor_user.txt"

GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GOOGLE_MODEL = "gemini-3.5-flash-lite"
MAX_RETRIES = 3
CACHE_TTL_SECONDS = 24 * 60 * 60

# Serialise advisor calls and enforce a minimum gap between them so the
# Gemini free tier does not 429 when the UI pages through notes quickly.
MIN_CALL_INTERVAL_SECONDS = 1.5
_call_lock = threading.Lock()
_last_call_time = [0.0]

SYSTEM_PROMPT = (
    "You are a preventive-health advisor writing short, general lifestyle "
    "guidance for a list of clinical conditions. You are NOT diagnosing, "
    "prescribing, or altering the conditions.\n\n"
    "Rules:\n"
    "1. Return only general lifestyle, monitoring, and prevention guidance.\n"
    "2. Do NOT include drug names, dosages, or treatment plans.\n"
    "3. Do NOT change or reinterpret the diagnosis.\n"
    "4. Keep each tip under 20 words. Aim for 2–3 tips per condition.\n"
    "5. If a condition is unfamiliar or non-actionable (e.g. 'ligature "
    "mark', 'contusion'), return an empty tips list for it.\n"
    "6. Write in plain language for a non-specialist reader.\n"
    "7. Return JSON only, matching the schema provided."
)


def _load_user_prompt_template() -> str:
    try:
        return _ADVICE_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "Conditions:\n{conditions}\n\n"
            "Return a JSON object with a single key `advice`, whose value is "
            "a list of objects with keys `condition` (verbatim from the input) "
            "and `tips` (list of short strings). Example:\n"
            '{"advice": [{"condition": "asthma", "tips": ["Avoid known triggers such as smoke and dust.", "Consider a peak-flow log to track control."]}]}'
        )


def _cache_key(condition_key: str) -> str:
    h = hashlib.sha256()
    h.update(GOOGLE_MODEL.encode("utf-8"))
    h.update(b"|")
    h.update(SYSTEM_PROMPT.encode("utf-8"))
    h.update(b"|")
    h.update(condition_key.encode("utf-8"))
    return f"advice:{h.hexdigest()}"


def _redis_get(key: str) -> dict | None:
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, db=0,
                        socket_connect_timeout=1.0, socket_timeout=1.0)
        raw = r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        return None


def _redis_set(key: str, value: dict) -> None:
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, db=0,
                        socket_connect_timeout=1.0, socket_timeout=1.0)
        r.setex(key, CACHE_TTL_SECONDS, json.dumps(value))
    except Exception:
        pass


def _throttle() -> None:
    """Enforce a minimum interval between Gemini calls.

    Called before every outbound request. Serialises concurrent callers
    through a module-level lock and sleeps if the previous call happened
    less than MIN_CALL_INTERVAL_SECONDS ago.
    """
    with _call_lock:
        now = time.time()
        elapsed = now - _last_call_time[0]
        if elapsed < MIN_CALL_INTERVAL_SECONDS:
            time.sleep(MIN_CALL_INTERVAL_SECONDS - elapsed)
        _last_call_time[0] = time.time()


def _call_gemini(conditions: list[str]) -> dict | None:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return None

    # Use .replace() instead of .format() so JSON braces in the template
    # (like {"advice": [...]}) are not treated as format placeholders.
    conditions_block = "\n".join(f"- {c}" for c in conditions)
    user_prompt = _load_user_prompt_template().replace("{conditions}", conditions_block)

    url = GOOGLE_API_URL.format(model=GOOGLE_MODEL)
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "temperature": 0.3,
            "responseMimeType": "application/json",
        },
    }

    for attempt in range(MAX_RETRIES + 1):
        _throttle()
        try:
            r = httpx.post(url, params={"key": api_key}, json=body, timeout=30.0)
            if r.status_code != 200:
                if r.status_code == 429 or r.status_code >= 500:
                    # Give the free tier a longer window for rate limits.
                    sleep_for = 5 if r.status_code == 429 else min(2 ** attempt, 8)
                    time.sleep(sleep_for)
                    continue
                return None
            data = r.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text)
        except Exception:
            if attempt < MAX_RETRIES:
                time.sleep(min(2 ** attempt, 8))
                continue
            return None
    return None


def generate(diagnoses: list[str]) -> dict | None:
    """Return a dict shaped `{"advice": [...], "disclaimer": "..."}` or None.

    diagnoses: list of normalised diagnosis names. Duplicates removed,
    sorted for cache stability.
    """
    clean = sorted({d.strip().lower() for d in diagnoses if d and d.strip()})
    if not clean:
        return None

    key = _cache_key("|".join(clean))
    cached = _redis_get(key)
    if cached is not None:
        return cached

    raw = _call_gemini(clean)
    if raw is None:
        return None

    # Sanitize: keep only items with a condition and at least one tip
    advice_list = []
    for item in raw.get("advice", []):
        if not isinstance(item, dict):
            continue
        cond = item.get("condition")
        tips = item.get("tips")
        if not cond or not isinstance(tips, list):
            continue
        tips = [t for t in tips if isinstance(t, str) and t.strip()]
        if not tips:
            continue
        advice_list.append({
            "condition": str(cond)[:80],
            "tips": [t.strip()[:160] for t in tips[:3]],
        })

    if not advice_list:
        return None

    result = {
        "advice": advice_list,
        "disclaimer": (
            "Our recommendations — general lifestyle and preventive guidance "
            "generated by our system. Not extracted from this note and not a "
            "substitute for clinical judgement."
        ),
    }
    _redis_set(key, result)
    return result