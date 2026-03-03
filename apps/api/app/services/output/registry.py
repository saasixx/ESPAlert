"""Registro de conectores de salida — patrón plugin para canales de notificación."""

import logging
from typing import Optional

from app.services.output.base import OutputConnector, OutputMessage

logger = logging.getLogger(__name__)


class OutputRegistry:
    """
    Registro singleton de conectores de salida.

    Uso:
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
        """Registra un conector de salida."""
        self._connectors[connector.name] = connector
        logger.info("Conector de salida registrado: %s", connector.name)

    def unregister(self, name: str) -> None:
        """Des-registra un conector de salida."""
        self._connectors.pop(name, None)

    def get(self, name: str) -> Optional[OutputConnector]:
        """Obtiene un conector por nombre."""
        return self._connectors.get(name)

    @property
    def available(self) -> list[str]:
        """Lista de conectores registrados."""
        return list(self._connectors.keys())

    async def dispatch(self, message: OutputMessage, channel: str, target: str) -> bool:
        """Envía un mensaje a través de un canal específico."""
        connector = self._connectors.get(channel)
        if not connector:
            logger.warning("Conector '%s' no registrado. Disponibles: %s", channel, self.available)
            return False
        try:
            return await connector.send(message, target)
        except Exception as e:
            logger.exception("Error en conector '%s' → %s: %s", channel, target, e)
            return False

    async def broadcast(
        self, message: OutputMessage, targets: dict[str, list[str]]
    ) -> dict[str, dict[str, bool]]:
        """
        Envía un mensaje a múltiples canales y destinos.

        Args:
            targets: {"telegram": ["@ch1", "@ch2"], "discord": ["url1"]}

        Returns:
            {"telegram": {"@ch1": True, "@ch2": False}, ...}
        """
        results: dict[str, dict[str, bool]] = {}
        for channel, channel_targets in targets.items():
            connector = self._connectors.get(channel)
            if not connector:
                logger.warning("Conector '%s' no encontrado, omitiendo.", channel)
                results[channel] = {t: False for t in channel_targets}
                continue
            results[channel] = await connector.send_batch(message, channel_targets)
        return results
