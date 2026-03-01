"""Unit tests for the normalizer service."""

import pytest
from datetime import datetime, timezone

from app.services.normalizer import Normalizer, SEVERITY_MAP, TYPE_MAP


def test_severity_map_completeness():
    """All severity values have mappings."""
    expected = {"green", "yellow", "orange", "red"}
    assert expected == set(SEVERITY_MAP.keys())


def test_type_map_has_other():
    """Event type map includes 'other' fallback."""
    assert "other" in TYPE_MAP


def test_parse_datetime_none():
    """Parsing None returns None."""
    assert Normalizer._parse_datetime(None) is None


def test_parse_datetime_already_datetime():
    """Passing a datetime returns it directly."""
    now = datetime.now(timezone.utc)
    assert Normalizer._parse_datetime(now) == now


def test_parse_datetime_iso():
    """ISO format strings are parsed."""
    result = Normalizer._parse_datetime("2024-01-15T10:30:00+00:00")
    assert result is not None
    assert result.year == 2024
    assert result.month == 1
