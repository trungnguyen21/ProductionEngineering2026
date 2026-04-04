import os
import json
import logging
import redis

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis():
    """Get or create a Redis client. Returns None if Redis is unavailable."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        try:
            _redis_client = redis.from_url(redis_url, decode_responses=True, socket_timeout=1)
            _redis_client.ping()
            logger.info("Redis connected at %s", redis_url)
        except Exception as e:
            logger.warning("Redis unavailable (%s), caching disabled", e)
            _redis_client = None
    return _redis_client


def cache_get(key: str):
    """Get a value from cache. Returns None on miss or if Redis is down."""
    r = get_redis()
    if r is None:
        return None
    try:
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def cache_set(key: str, value, ttl_seconds: int = 300):
    """Set a value in cache with TTL. Silently fails if Redis is down."""
    r = get_redis()
    if r is None:
        return
    try:
        r.setex(key, ttl_seconds, json.dumps(value))
    except Exception:
        pass


def cache_delete(key: str):
    """Delete a key from cache. Silently fails if Redis is down."""
    r = get_redis()
    if r is None:
        return
    try:
        r.delete(key)
    except Exception:
        pass
