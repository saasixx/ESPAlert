"""Redis cache helpers for hot API endpoints."""

import hashlib
import json
import logging
from typing import Any

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

CACHE_TTL_EVENTS = 300  # 5 min — matches fastest poll interval (IGN 2 min, rounded up)
CACHE_TTL_SUMMARY = 60  # 1 min — summary changes more frequently

_PREFIX = "espalert:cache"
_KEY_EVENTS_GLOB = f"{_PREFIX}:events:*"
KEY_SUMMARY = f"{_PREFIX}:summary"


def events_cache_key(params: dict) -> str:
    """Derive a stable cache key from query parameters."""
    canonical = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.md5(canonical.encode()).hexdigest()
    return f"{_PREFIX}:events:{digest}"


async def get_cached(redis: aioredis.Redis, key: str) -> Any | None:
    """Return deserialized cached value or None on miss/error."""
    try:
        raw = await redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Cache read error for %s: %s", key, exc)
        return None


async def set_cached(redis: aioredis.Redis, key: str, data: Any, ttl: int) -> None:
    """Serialize and store data in Redis with TTL. Silently ignores errors."""
    try:
        await redis.set(key, json.dumps(data, default=str), ex=ttl)
    except Exception as exc:
        logger.warning("Cache write error for %s: %s", key, exc)


async def invalidate_events_cache(redis: aioredis.Redis) -> None:
    """Delete all /events/ cache entries and the summary key."""
    try:
        # SCAN-based deletion to avoid blocking on large keyspaces
        cursor = 0
        deleted = 0
        while True:
            cursor, keys = await redis.scan(cursor, match=_KEY_EVENTS_GLOB, count=100)
            if keys:
                await redis.delete(*keys)
                deleted += len(keys)
            if cursor == 0:
                break

        await redis.delete(KEY_SUMMARY)
        logger.debug("Cache invalidated: %d event keys + summary", deleted)
    except Exception as exc:
        logger.warning("Cache invalidation error: %s", exc)
