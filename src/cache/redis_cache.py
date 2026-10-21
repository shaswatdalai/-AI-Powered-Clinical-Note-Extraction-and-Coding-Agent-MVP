
"""
Redis-backed result cache for pipeline runs.

If Redis is available, results are cached for 24 hours.
If Redis or its Python package is unavailable, the app
continues normally without caching.

Configuration:
- Redis Cloud: set REDIS_HOST, REDIS_PORT, REDIS_USERNAME,
  and REDIS_PASSWORD. TLS is enabled by default when credentials
  are configured.
- Local development: without cloud credentials, defaults to
  localhost:6379.
"""

import hashlib
import json
import os
from typing import Optional

# Redis is optional. Do not crash if its package is missing.
try:
    import redis as _redis
    _REDIS_AVAILABLE = True
except ImportError:
    _redis = None
    _REDIS_AVAILABLE = False


# Read configuration from environment variables.
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_USERNAME = os.getenv("REDIS_USERNAME")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Enable TLS by default when Redis Cloud credentials are configured.
# Set REDIS_SSL=false only if your provider requires a non-TLS connection.
_cloud_credentials_configured = bool(
    REDIS_USERNAME and REDIS_PASSWORD
)
REDIS_SSL = os.getenv(
    "REDIS_SSL",
    "true" if _cloud_credentials_configured else "false",
).strip().lower() in {"1", "true", "yes", "on"}

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
        client_options = {
            "host": REDIS_HOST,
            "port": REDIS_PORT,
            "db": REDIS_DB,
            "socket_connect_timeout": 3.0,
            "socket_timeout": 3.0,
            "decode_responses": False,
        }

        if REDIS_USERNAME:
            client_options["username"] = REDIS_USERNAME

        if REDIS_PASSWORD:
            client_options["password"] = REDIS_PASSWORD

        if REDIS_SSL:
            client_options["ssl"] = True

        client = _redis.Redis(**client_options)
        client.ping()

        _client = client
        _connection_ok = True
        return _client

    except Exception:
        # Redis failure must not crash the application.
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

    return hashlib.sha256(
        blob.encode("utf-8")
    ).hexdigest()[:16]


def _key(note_id: str, note_text: str) -> str:
    h = hashlib.sha256()
    h.update(note_id.encode("utf-8"))
    h.update(b"|")
    h.update(_prompt_hash().encode("utf-8"))
    h.update(b"|")
    h.update(note_text.encode("utf-8"))

    return f"pipeline:{h.hexdigest()}"


def get_result(
    note_id: str,
    note_text: str,
) -> Optional[dict]:
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

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")

        return json.loads(raw)

    except Exception:
        return None


def set_result(
    note_id: str,
    note_text: str,
    result: dict,
) -> None:
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
            "hit_rate": round(hits / total, 3)
            if total else 0.0,
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
