"""Tests for the output connectors framework."""

from datetime import datetime, timezone

from app.services.output.base import OutputMessage, OutputConnector
from app.services.output.registry import OutputRegistry


class FakeConnector(OutputConnector):
    """Fake connector for tests."""

    def __init__(self):
        self.sent: list[tuple[OutputMessage, str]] = []

    @property
    def name(self) -> str:
        return "fake"

    async def send(self, message: OutputMessage, target: str) -> bool:
        self.sent.append((message, target))
        return True


def _sample_message() -> OutputMessage:
    return OutputMessage(
        event_id="test-123",
        title="Terremoto M4.2 — Granada",
        severity="orange",
        event_type="earthquake",
        description="Terremoto moderado cerca de Granada",
        area_name="Granada, Andalucía",
        magnitude="4.2",
        depth_km="10",
        effective=datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc),
    )


def test_output_message_severity_emoji():
    msg = _sample_message()
    assert msg.severity_emoji == "🟠"


def test_output_message_type_emoji():
    msg = _sample_message()
    assert msg.type_emoji == "📳"


def test_output_message_format_text():
    msg = _sample_message()
    text = msg.format_text()
    assert "Terremoto M4.2" in text
    assert "Granada" in text
    assert "4.2" in text


def test_output_message_format_html():
    msg = _sample_message()
    html = msg.format_html()
    assert "<b>" in html
    assert "Terremoto M4.2" in html


async def test_registry_dispatch():
    # Clear singleton for test
    OutputRegistry._instance = None
    registry = OutputRegistry()

    fake = FakeConnector()
    registry.register(fake)

    msg = _sample_message()
    result = await registry.dispatch(msg, channel="fake", target="@test")

    assert result is True
    assert len(fake.sent) == 1
    assert fake.sent[0][1] == "@test"

    # Cleanup
    OutputRegistry._instance = None


async def test_registry_unknown_channel():
    OutputRegistry._instance = None
    registry = OutputRegistry()

    msg = _sample_message()
    result = await registry.dispatch(msg, channel="nonexistent", target="x")
    assert result is False

    OutputRegistry._instance = None


async def test_registry_broadcast():
    OutputRegistry._instance = None
    registry = OutputRegistry()

    fake = FakeConnector()
    registry.register(fake)

    msg = _sample_message()
    results = await registry.broadcast(msg, targets={"fake": ["@ch1", "@ch2"]})

    assert results["fake"]["@ch1"] is True
    assert results["fake"]["@ch2"] is True
    assert len(fake.sent) == 2

    OutputRegistry._instance = None
