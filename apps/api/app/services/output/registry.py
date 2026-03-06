"""Output connector registry — plugin pattern for notification channels."""

import logging
from typing import Optional

from app.services.output.base import OutputConnector, OutputMessage

logger = logging.getLogger(__name__)


class OutputRegistry:
    """
    Singleton registry of output connectors.

    Usage:
        registry = OutputRegistry()
        registry.register(TelegramConnector(bot_token="..."))
        registry.register(DiscordConnector(webhook_url="..."))

        await registry.dispatch(message, channel="telegram", target="@channel_id")
        await registry.broadcast(message, targets={"telegram": ["@ch1"], "discord": ["url"]})
    """

    _instance: Optional["OutputRegistry"] = None

    def __new__(cls) -> "OutputRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connectors = {}
        return cls._instance

    def register(self, connector: OutputConnector) -> None:
        """Register an output connector."""
        self._connectors[connector.name] = connector
        logger.info("Output connector registered: %s", connector.name)

    def unregister(self, name: str) -> None:
        """Unregister an output connector."""
        self._connectors.pop(name, None)

    def get(self, name: str) -> Optional[OutputConnector]:
        """Get a connector by name."""
        return self._connectors.get(name)

    @property
    def available(self) -> list[str]:
        """List of registered connectors."""
        return list(self._connectors.keys())

    async def dispatch(self, message: OutputMessage, channel: str, target: str) -> bool:
        """Send a message through a specific channel."""
        connector = self._connectors.get(channel)
        if not connector:
            logger.warning("Connector '%s' not registered. Available: %s", channel, self.available)
            return False
        try:
            return await connector.send(message, target)
        except Exception as e:
            logger.exception("Error in connector '%s' → %s: %s", channel, target, e)
            return False

    async def broadcast(self, message: OutputMessage, targets: dict[str, list[str]]) -> dict[str, dict[str, bool]]:
        """
        Send a message to multiple channels and targets.

        Args:
            targets: {"telegram": ["@ch1", "@ch2"], "discord": ["url1"]}

        Returns:
            {"telegram": {"@ch1": True, "@ch2": False}, ...}
        """
        results: dict[str, dict[str, bool]] = {}
        for channel, channel_targets in targets.items():
            connector = self._connectors.get(channel)
            if not connector:
                logger.warning("Connector '%s' not found, skipping.", channel)
                results[channel] = {t: False for t in channel_targets}
                continue
            results[channel] = await connector.send_batch(message, channel_targets)
        return results
