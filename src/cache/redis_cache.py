"""
Redis-backed result cache for pipeline runs.

Wraps the reviewer interface's per-note pipeline calls. If Redis is
available (Redis server on localhost:6379), results are cached for 24h
and re-runs are instant. If Redis is unavailable, the module silently
falls back to running the pipeline normally — no crash, no error.

Key structure:
    pipeline:<sha256(note_id | prompt_hash | note_text)>  -> JSON result
    stats:hits                                            -> counter
    stats:misses                                          -> counter

The prompt_hash includes the extractor and verifier system prompts plus
the guardrails/schema fingerprints. Editing a prompt invalidates every
cached result automatically.
"""

import hashlib
import json
from pathlib import Path
from typing import Optional

import redis

try:
    import redis as _redis
    _REDIS_AVAILABLE = True
except ImportError:
    _redis = None
    _REDIS_AVAILABLE = False


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
TTL_SECONDS = 24 * 60 * 60  # 24 hours


_client: Optional[" redis.Redis"] = None
_connection_ok: Optional[bool] = None


def _get_client():
    """Return a live Redis client, or None if Redis is unreachable."""
    global _client, _connection_ok

    if not _REDIS_AVAILABLE:
        return None
    if _client is not None and _connection_ok:
        return _client

    try:
        c = _redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB,
                         socket_connect_timeout=1.0, socket_timeout=1.0)
        c.ping()
        _client = c
        _connection_ok = True
        return _client
    except Exception:
        _connection_ok = False
        return None


def is_available() -> bool:
    """Public check used by the UI to display a Redis status indicator."""
    return _get_client() is not None


def _prompt_hash() -> str:
    """Hash of the current extractor + verifier prompts and schema/guardrails.

    Cached results are keyed partly on this, so editing any prompt
    invalidates the cache. Falls back to a static string if the prompt
    files cannot be read (defensive; should not happen in practice).
    """
    try:
        from src.extractor import SYSTEM_PROMPT as EX_SYS, USER_PROMPT_TEMPLATE as EX_USR
        from src.verifier import SYSTEM_PROMPT as VF_SYS, USER_PROMPT_TEMPLATE as VF_USR
        from src.extractor import _guardrails_fingerprint
        from src.verifier import _schema_fingerprint
        blob = "|".join([EX_SYS, EX_USR, VF_SYS, VF_USR,
                         _guardrails_fingerprint(), _schema_fingerprint()])
    except Exception:
        blob = "static"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _key(note_id: str, note_text: str) -> str:
    h = hashlib.sha256()
    h.update(note_id.encode("utf-8"))
    h.update(b"|")
    h.update(_prompt_hash().encode("utf-8"))
    h.update(b"|")
    h.update(note_text.encode("utf-8"))
    return f"pipeline:{h.hexdigest()}"


def get_result(note_id: str, note_text: str) -> Optional[dict]:
    """Return a cached pipeline result, or None if not present / Redis down."""
    c = _get_client()
    if c is None:
        return None
    try:
        raw = c.get(_key(note_id, note_text))
        if raw is None:
            _bump_stat(c, "misses")
            return None
        _bump_stat(c, "hits")
        return json.loads(raw)
    except Exception:
        return None


def set_result(note_id: str, note_text: str, result: dict) -> None:
    """Store a pipeline result in Redis. Silent no-op if Redis is down."""
    c = _get_client()
    if c is None:
        return
    try:
        c.setex(_key(note_id, note_text), TTL_SECONDS, json.dumps(result))
    except Exception:
        pass


def _bump_stat(c, name: str) -> None:
    try:
        c.incr(f"stats:{name}")
    except Exception:
        pass


def stats() -> dict:
    """Return the current hit/miss stats and the Redis availability flag."""
    c = _get_client()
    if c is None:
        return {"redis_available": False, "hits": 0, "misses": 0, "hit_rate": 0.0}
    try:
        hits = int(c.get("stats:hits") or 0)
        misses = int(c.get("stats:misses") or 0)
        total = hits + misses
        return {
            "redis_available": True,
            "hits": hits,
            "misses": misses,
            "hit_rate": round(hits / total, 3) if total else 0.0,
        }
    except Exception:
        return {"redis_available": False, "hits": 0, "misses": 0, "hit_rate": 0.0}


def reset_stats() -> None:
    c = _get_client()
    if c is None:
        return
    try:
        c.delete("stats:hits", "stats:misses")
    except Exception:
        pass


def flush() -> None:
    """Delete every pipeline:* key. Does not touch other Redis data."""
    c = _get_client()
    if c is None:
        return
    try:
        for k in c.scan_iter("pipeline:*"):
            c.delete(k)
    except Exception:
        pass