"""Integration tests for Normalizer deduplication logic."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.event import Event, EventSource, EventType, Severity
from app.services.normalizer import Normalizer


def _make_raw(
    source_id: str = "test-001",
    severity: str = "green",
    event_type: str = "other",
    source: str = "aemet",
    title: str = "Test Event",
    description: str = "A test event",
    effective: str = "2024-06-01T10:00:00+00:00",
    expires: str = "2024-06-01T18:00:00+00:00",
    location: str = "POINT(-3.7 40.4)",
    area_name: str = "Madrid",
) -> dict:
    """Helper to build a raw event dict."""
    return {
        "source_id": source_id,
        "severity": severity,
        "event_type": event_type,
        "source": source,
        "title": title,
        "description": description,
        "effective": effective,
        "expires": expires,
        "area_wkt": location,
        "area_name": area_name,
    }


def _make_db_event(source_id: str, severity=Severity.GREEN, description: str = "A test event", expires=None) -> Event:
    """Helper to create an in-memory Event model (no DB)."""
    event = Event.__new__(Event)
    event.source_id = source_id
    event.severity = severity
    event.description = description
    event.expires = expires or datetime(2024, 6, 1, 18, 0, 0, tzinfo=timezone.utc)
    event.source = EventSource.AEMET
    event.event_type = EventType.OTHER
    event.title = "Test Event"
    event.instructions = None
    event.area = None
    event.area_name = "Madrid"
    event.effective = datetime(2024, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    event.source_url = None
    event.magnitude = None
    event.depth_km = None
    event.raw_data = None
    return event


def _make_normalizer(existing_event=None):
    """Build a Normalizer with a mocked AsyncSession."""
    db = AsyncMock()

    scalar_mock = MagicMock()
    scalar_mock.scalar_one_or_none.return_value = existing_event

    execute_mock = AsyncMock(return_value=scalar_mock)
    db.execute = execute_mock
    db.add = MagicMock()
    db.flush = AsyncMock()

    return Normalizer(db=db)


# ---------------------------------------------------------------------------
# Deduplication: duplicate event is skipped
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_event_is_skipped():
    """A second event with the same source_id and no field changes returns nothing."""
    existing = _make_db_event("dup-001")
    normalizer = _make_normalizer(existing_event=existing)

    raw = _make_raw(
        source_id="dup-001",
        severity="green",
        description="A test event",
        expires="2024-06-01T18:00:00+00:00",
    )

    results = await normalizer.process_events([raw])

    # No new event created, flush should not be called
    assert results == []
    normalizer.db.flush.assert_not_called()


# ---------------------------------------------------------------------------
# Deduplication: new event is inserted
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_new_event_is_inserted():
    """An event with a new source_id is inserted and returned."""
    normalizer = _make_normalizer(existing_event=None)

    raw = _make_raw(source_id="new-001")
    results = await normalizer.process_events([raw])

    assert len(results) == 1
    assert results[0].source_id == "new-001"
    normalizer.db.add.assert_called_once()
    normalizer.db.flush.assert_awaited_once()


# ---------------------------------------------------------------------------
# Deduplication: location and timestamp are preserved on duplicate
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_preserves_location_and_timestamp():
    """When a duplicate is skipped, the existing event's values are untouched."""
    original_expires = datetime(2024, 6, 1, 18, 0, 0, tzinfo=timezone.utc)
    existing = _make_db_event("loc-001", expires=original_expires)
    normalizer = _make_normalizer(existing_event=existing)

    # Send the exact same event again
    raw = _make_raw(
        source_id="loc-001",
        severity="green",
        description="A test event",
        expires="2024-06-01T18:00:00+00:00",
    )

    await normalizer.process_events([raw])

    # The existing event's expires should not have changed
    assert existing.expires == original_expires


# ---------------------------------------------------------------------------
# Update: severity change triggers an update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_with_new_severity_is_updated():
    """An existing event with a changed severity is updated and returned."""
    existing = _make_db_event("upd-001", severity=Severity.GREEN)
    normalizer = _make_normalizer(existing_event=existing)

    raw = _make_raw(source_id="upd-001", severity="red", description="A test event")

    results = await normalizer.process_events([raw])

    assert len(results) == 1
    assert results[0].severity == Severity.RED


# ---------------------------------------------------------------------------
# Update: description change triggers an update
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_with_new_description_is_updated():
    """An existing event with a changed description is updated and returned."""
    existing = _make_db_event("upd-002", description="Old description")
    normalizer = _make_normalizer(existing_event=existing)

    raw = _make_raw(source_id="upd-002", description="New description")

    results = await normalizer.process_events([raw])

    assert len(results) == 1
    assert results[0].description == "New description"


# ---------------------------------------------------------------------------
# Edge case: missing source_id is skipped
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_event_without_source_id_is_skipped():
    """A raw event dict with no source_id is silently skipped."""
    normalizer = _make_normalizer(existing_event=None)

    raw = _make_raw(source_id="")  # empty source_id

    results = await normalizer.process_events([raw])

    assert results == []
    normalizer.db.add.assert_not_called()


# ---------------------------------------------------------------------------
# Batch: mix of new and duplicate events
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_batch_with_mixed_new_and_duplicate():
    """A batch of events where some are new and some are duplicates."""
    existing = _make_db_event("batch-dup")

    call_count = 0
    original_execute = None

    db = AsyncMock()

    async def execute_side_effect(stmt):
        nonlocal call_count
        call_count += 1
        scalar_mock = MagicMock()
        # First call → duplicate, second call → new
        scalar_mock.scalar_one_or_none.return_value = existing if call_count == 1 else None
        return scalar_mock

    db.execute = execute_side_effect
    db.add = MagicMock()
    db.flush = AsyncMock()

    normalizer = Normalizer(db=db)

    raws = [
        _make_raw(source_id="batch-dup"),   # duplicate, same fields → skip
        _make_raw(source_id="batch-new"),   # new → insert
    ]

    results = await normalizer.process_events(raws)

    assert len(results) == 1
    assert results[0].source_id == "batch-new"
