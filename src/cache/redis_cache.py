
"""
Redis-backed result cache for pipeline runs.

If Redis is available, results are cached for 24 hours.
If Redis or its Python package is unavailable, the app
continues normally without caching.
"""

import hashlib
import json
from typing import Optional

# Redis is optional. Do not crash if its package is missing.
try:
    import redis as _redis
    _REDIS_AVAILABLE = True
except ImportError:
    _redis = None
    _REDIS_AVAILABLE = False


REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
TTL_SECONDS = 24 * 60 * 60

_client = None
_connection_ok = None


def _get_client():
    """Return a working Redis client, or None if unavailable."""
    global _client, _connection_ok

    if not _REDIS_AVAILABLE:
        return None

    if _client is not None and _connection_ok:
        return _client

    try:
        client = _redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            socket_connect_timeout=1.0,
            socket_timeout=1.0,
        )
        client.ping()
        _client = client
        _connection_ok = True
        return _client
    except Exception:
        _connection_ok = False
        return None


def is_available() -> bool:
    return _get_client() is not None


def _prompt_hash() -> str:
    """Hash prompts and schema fingerprints to invalidate stale cache."""
    try:
        from src.extractor import (
            SYSTEM_PROMPT as EX_SYS,
            USER_PROMPT_TEMPLATE as EX_USR,
            _guardrails_fingerprint,
        )
        from src.verifier import (
            SYSTEM_PROMPT as VF_SYS,
            USER_PROMPT_TEMPLATE as VF_USR,
            _schema_fingerprint,
        )

        blob = "|".join([
            EX_SYS,
            EX_USR,
            VF_SYS,
            VF_USR,
            _guardrails_fingerprint(),
            _schema_fingerprint(),
        ])
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
    """Return cached result, or None if absent/unavailable."""
    client = _get_client()
    if client is None:
        return None

    try:
        raw = client.get(_key(note_id, note_text))
        if raw is None:
            _bump_stat(client, "misses")
            return None

        _bump_stat(client, "hits")
        return json.loads(raw)
    except Exception:
        return None


def set_result(note_id: str, note_text: str, result: dict) -> None:
    """Cache a result if Redis is available; otherwise do nothing."""
    client = _get_client()
    if client is None:
        return

    try:
        client.setex(
            _key(note_id, note_text),
            TTL_SECONDS,
            json.dumps(result),
        )
    except Exception:
        pass


def _bump_stat(client, name: str) -> None:
    try:
        client.incr(f"stats:{name}")
    except Exception:
        pass


def stats() -> dict:
    """Return cache statistics and Redis availability."""
    client = _get_client()

    if client is None:
        return {
            "redis_available": False,
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
        }

    try:
        hits = int(client.get("stats:hits") or 0)
        misses = int(client.get("stats:misses") or 0)
        total = hits + misses

        return {
            "redis_available": True,
            "hits": hits,
            "misses": misses,
            "hit_rate": round(hits / total, 3) if total else 0.0,
        }
    except Exception:
        return {
            "redis_available": False,
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0,
        }


def reset_stats() -> None:
    client = _get_client()
    if client is None:
        return

    try:
        client.delete("stats:hits", "stats:misses")
    except Exception:
        pass


def flush() -> None:
    """Delete pipeline cache entries without touching other Redis data."""
    client = _get_client()
    if client is None:
        return

    try:
        for key in client.scan_iter("pipeline:*"):
            client.delete(key)
    except Exception:
        pass
