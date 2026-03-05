"""Abstract base class for output connectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class OutputMessage:
    """Normalized message sent to an output connector."""

    event_id: str
    title: str
    severity: str  # green | yellow | orange | red
    event_type: str
    description: str = ""
    instructions: str = ""
    area_name: str = ""
    source_url: str = ""
    magnitude: Optional[str] = None
    depth_km: Optional[str] = None
    effective: Optional[datetime] = None
    expires: Optional[datetime] = None
    extra: dict = field(default_factory=dict)

    @property
    def severity_emoji(self) -> str:
        return {"red": "🔴", "orange": "🟠", "yellow": "🟡", "green": "🟢"}.get(
            self.severity, "⚪"
        )

    @property
    def type_emoji(self) -> str:
        return {
            "wind": "💨", "rain": "🌧️", "storm": "⛈️", "snow": "❄️",
            "ice": "🧊", "fog": "🌫️", "heat": "🌡️", "cold": "🥶",
            "earthquake": "📳", "tsunami": "🌊", "coastal": "🌊",
            "traffic_accident": "🚗", "traffic_closure": "🚧",
            "traffic_works": "🔧", "traffic_jam": "🐌",
            "fire_risk": "🔥", "civil_protection": "🚨",
        }.get(self.event_type, "⚠️")

    def format_text(self, include_url: bool = True) -> str:
        """Format the message as plain text."""
        lines = [
            f"{self.severity_emoji} {self.type_emoji} {self.title}",
        ]
        if self.area_name:
            lines.append(f"📍 {self.area_name}")
        if self.magnitude:
            lines.append(f"Magnitud: {self.magnitude}")
            if self.depth_km:
                lines[-1] += f" • Profundidad: {self.depth_km} km"
        if self.description:
            # Truncate long description
            desc = self.description[:300]
            if len(self.description) > 300:
                desc += "…"
            lines.append(desc)
        if self.instructions:
            lines.append(f"ℹ️ {self.instructions[:200]}")
        if include_url and self.source_url:
            lines.append(f"🔗 {self.source_url}")
        return "\n".join(lines)

    def format_html(self) -> str:
        """Format the message as basic HTML."""
        parts = [
            f"<b>{self.severity_emoji} {self.type_emoji} {self.title}</b>",
        ]
        if self.area_name:
            parts.append(f"📍 <i>{self.area_name}</i>")
        if self.magnitude:
            mag = f"Magnitud: <b>{self.magnitude}</b>"
            if self.depth_km:
                mag += f" • Profundidad: {self.depth_km} km"
            parts.append(mag)
        if self.description:
            parts.append(self.description[:500])
        if self.instructions:
            parts.append(f"<i>ℹ️ {self.instructions[:200]}</i>")
        if self.source_url:
            parts.append(f'<a href="{self.source_url}">Fuente</a>')
        return "\n".join(parts)


class OutputConnector(ABC):
    """Base interface for all output connectors."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Connector name (e.g. 'telegram', 'discord', 'email')."""
        ...

    @abstractmethod
    async def send(self, message: OutputMessage, target: str) -> bool:
        """
        Send a message to the specified target.

        Args:
            message: Normalized alert message.
            target: Target identifier (chat_id, webhook_url, email, etc).

        Returns:
            True if the send was successful.
        """
        ...

    async def send_batch(self, message: OutputMessage, targets: list[str]) -> dict[str, bool]:
        """Send a message to multiple targets. Returns target→success map."""
        results = {}
        for target in targets:
            try:
                results[target] = await self.send(message, target)
            except Exception:
                results[target] = False
        return results
