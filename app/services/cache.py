import json
import logging
import os
import time
from typing import Optional

import redis

from app.observability.metrics import (
    CACHE_HITS_TOTAL,
    CACHE_MISSES_TOTAL,
    CACHE_OPERATION_DURATION_SECONDS,
    CACHE_OPERATIONS_TOTAL,
)

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None
_redis_ready: bool = False


def _observe_cache_operation(operation: str, result: str, duration_s: float) -> None:
    CACHE_OPERATIONS_TOTAL.labels(operation=operation, result=result).inc()
    CACHE_OPERATION_DURATION_SECONDS.labels(operation=operation, result=result).observe(duration_s)


def init_cache(app=None) -> Optional[redis.Redis]:
    """Initialize Redis client once at app startup. Returns None if unavailable."""
    global _redis_client, _redis_ready

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    try:
        client = redis.from_url(redis_url, decode_responses=True, socket_timeout=1)
        client.ping()
        _redis_client = client
        _redis_ready = True
        logger.info("redis.connected", extra={"redis_url": redis_url})
    except Exception as exc:
        _redis_client = None
        _redis_ready = False
        logger.warning("redis.unavailable", extra={"error_type": type(exc).__name__})

    if app is not None:
        app.extensions = getattr(app, "extensions", {})
        app.extensions["redis_client"] = _redis_client
        app.extensions["redis_ready"] = _redis_ready

    return _redis_client


def get_redis() -> Optional[redis.Redis]:
    """Return startup-initialized Redis client, or None if unavailable."""
    return _redis_client


def is_redis_ready() -> bool:
    return _redis_ready and _redis_client is not None


def check_redis_connection() -> bool:
    """Active Redis connectivity check for readiness endpoints."""
    r = get_redis()
    if r is None:
        return False
    try:
        r.ping()
        return True
    except Exception as exc:
        logger.warning("redis.ping.failed", extra={"error_type": type(exc).__name__})
        return False


def cache_get(key: str):
    """Get a value from cache. Returns None on miss or if Redis is down."""
    started = time.perf_counter()
    r = get_redis()
    if r is None:
        duration_s = time.perf_counter() - started
        CACHE_MISSES_TOTAL.labels(cache_name="redis").inc()
        _observe_cache_operation("get", "backend_unavailable", duration_s)
        return None

    try:
        val = r.get(key)
        duration_s = time.perf_counter() - started

        if val:
            CACHE_HITS_TOTAL.labels(cache_name="redis").inc()
            _observe_cache_operation("get", "hit", duration_s)
            return json.loads(val)

        CACHE_MISSES_TOTAL.labels(cache_name="redis").inc()
        _observe_cache_operation("get", "miss", duration_s)
        return None
    except Exception as exc:
        duration_s = time.perf_counter() - started
        CACHE_MISSES_TOTAL.labels(cache_name="redis").inc()
        _observe_cache_operation("get", "error", duration_s)
        logger.warning("redis.get.failed", extra={"error_type": type(exc).__name__})
        return None


def cache_set(key: str, value, ttl_seconds: int = 300):
    """Set a value in cache with TTL. Silently fails if Redis is down."""
    started = time.perf_counter()
    r = get_redis()
    if r is None:
        _observe_cache_operation("set", "backend_unavailable", time.perf_counter() - started)
        return

    try:
        r.setex(key, ttl_seconds, json.dumps(value))
        _observe_cache_operation("set", "ok", time.perf_counter() - started)
    except Exception as exc:
        _observe_cache_operation("set", "error", time.perf_counter() - started)
        logger.warning("redis.set.failed", extra={"error_type": type(exc).__name__})


def cache_delete(key: str):
    """Delete a key or pattern (e.g. 'urls:*') from cache. Silently fails if Redis is down."""
    started = time.perf_counter()
    r = get_redis()
    if r is None:
        _observe_cache_operation("delete", "backend_unavailable", time.perf_counter() - started)
        return

    try:
        if "*" in key:
            keys = r.keys(key)
            if keys:
                r.delete(*keys)
        else:
            r.delete(key)
        _observe_cache_operation("delete", "ok", time.perf_counter() - started)
    except Exception as exc:
        _observe_cache_operation("delete", "error", time.perf_counter() - started)
        logger.warning("redis.delete.failed", extra={"error_type": type(exc).__name__})
