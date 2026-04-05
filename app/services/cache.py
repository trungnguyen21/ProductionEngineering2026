import json
import logging
import os
import time

import redis

from app.observability.metrics import (
    CACHE_HITS_TOTAL,
    CACHE_MISSES_TOTAL,
    CACHE_OPERATION_DURATION_SECONDS,
    CACHE_OPERATIONS_TOTAL,
)

logger = logging.getLogger(__name__)

_redis_client = None

def _observe_cache_operation(operation: str, result: str, duration_s: float) -> None:
    CACHE_OPERATIONS_TOTAL.labels(operation=operation, result=result).inc()
    CACHE_OPERATION_DURATION_SECONDS.labels(operation=operation, result=result).observe(duration_s)

def get_redis():
    """Get or create a Redis client. Returns None if Redis is unavailable."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            _redis_client = redis.from_url(redis_url, decode_responses=True, socket_timeout=1)
            _redis_client.ping()
            logger.info("redis.connected", extra={"redis_url": redis_url})
        except Exception as exc:
            logger.warning("redis.unavailable", extra={"error_type": type(exc).__name__})
            _redis_client = None
    return _redis_client

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
