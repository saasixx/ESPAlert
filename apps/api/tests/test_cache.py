"""Unit tests for the Redis cache service."""

from unittest.mock import AsyncMock

import pytest

from app.services.cache import (
    events_cache_key,
    get_cached,
    set_cached,
    invalidate_events_cache,
    KEY_SUMMARY,
)


def test_events_cache_key_is_stable():
    """Same params always produce the same key."""
    params = {"event_type": "wind", "severity": "red", "limit": 50}
    assert events_cache_key(params) == events_cache_key(params)


def test_events_cache_key_differs_by_params():
    """Different params produce different keys."""
    key1 = events_cache_key({"event_type": "wind"})
    key2 = events_cache_key({"event_type": "rain"})
    assert key1 != key2


def test_events_cache_key_order_independent():
    """Key is stable regardless of dict insertion order."""
    key1 = events_cache_key({"a": 1, "b": 2})
    key2 = events_cache_key({"b": 2, "a": 1})
    assert key1 == key2


@pytest.mark.asyncio
async def test_get_cached_miss():
    """Returns None on cache miss."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)

    result = await get_cached(redis, "espalert:cache:events:abc")
    assert result is None


@pytest.mark.asyncio
async def test_get_cached_hit():
    """Deserializes JSON on cache hit."""
    import json

    redis = AsyncMock()
    redis.get = AsyncMock(return_value=json.dumps([{"id": "123", "title": "Test"}]))

    result = await get_cached(redis, "espalert:cache:events:abc")
    assert result == [{"id": "123", "title": "Test"}]


@pytest.mark.asyncio
async def test_get_cached_redis_error_returns_none():
    """Redis errors are swallowed and return None (graceful degradation)."""
    redis = AsyncMock()
    redis.get = AsyncMock(side_effect=ConnectionError("Redis down"))

    result = await get_cached(redis, "espalert:cache:events:abc")
    assert result is None


@pytest.mark.asyncio
async def test_set_cached_calls_redis():
    """set_cached writes JSON with TTL."""
    import json

    redis = AsyncMock()
    redis.set = AsyncMock()

    await set_cached(redis, "espalert:cache:events:abc", [{"id": "1"}], 300)

    redis.set.assert_called_once()
    call_args = redis.set.call_args
    assert call_args[0][0] == "espalert:cache:events:abc"
    stored = json.loads(call_args[0][1])
    assert stored == [{"id": "1"}]
    assert call_args[1]["ex"] == 300


@pytest.mark.asyncio
async def test_set_cached_redis_error_is_silent():
    """Redis write errors do not propagate."""
    redis = AsyncMock()
    redis.set = AsyncMock(side_effect=ConnectionError("Redis down"))

    # Should not raise
    await set_cached(redis, "key", {"data": 1}, 60)


@pytest.mark.asyncio
async def test_invalidate_events_cache_deletes_keys():
    """invalidate_events_cache scans and deletes event keys + summary."""
    redis = AsyncMock()
    # First scan returns keys, cursor=0 (done)
    redis.scan = AsyncMock(return_value=(0, [b"espalert:cache:events:aaa", b"espalert:cache:events:bbb"]))
    redis.delete = AsyncMock()

    await invalidate_events_cache(redis)

    # Should have deleted the event keys
    redis.delete.assert_any_call(b"espalert:cache:events:aaa", b"espalert:cache:events:bbb")
    # Should also delete summary key
    redis.delete.assert_any_call(KEY_SUMMARY)


@pytest.mark.asyncio
async def test_invalidate_events_cache_no_keys():
    """invalidate_events_cache handles empty keyspace gracefully."""
    redis = AsyncMock()
    redis.scan = AsyncMock(return_value=(0, []))
    redis.delete = AsyncMock()

    await invalidate_events_cache(redis)

    # Only summary key deleted
    redis.delete.assert_called_once_with(KEY_SUMMARY)
