"""Discord output connector — sends alerts via Discord webhooks."""

import logging

import httpx

from app.services.output.base import OutputConnector, OutputMessage

logger = logging.getLogger(__name__)

# Discord embed colors (decimal)
SEVERITY_COLORS = {
    "red": 0xEF4444,
    "orange": 0xF97316,
    "yellow": 0xEAB308,
    "green": 0x22C55E,
}


class DiscordConnector(OutputConnector):
    """
    Send alerts to Discord via webhooks.

    Target: Full webhook URL (https://discord.com/api/webhooks/...)
    """

    @property
    def name(self) -> str:
        return "discord"

    async def send(self, message: OutputMessage, target: str) -> bool:
        embed = {
            "title": f"{message.severity_emoji} {message.type_emoji} {message.title}",
            "color": SEVERITY_COLORS.get(message.severity, 0x808080),
            "fields": [],
        }

        if message.area_name:
            embed["fields"].append({"name": "📍 Ubicación", "value": message.area_name, "inline": True})
        if message.magnitude:
            mag_val = message.magnitude
            if message.depth_km:
                mag_val += f" ({message.depth_km} km prof.)"
            embed["fields"].append({"name": "Magnitud", "value": mag_val, "inline": True})
        if message.description:
            embed["description"] = message.description[:2048]
        if message.instructions:
            embed["fields"].append({"name": "ℹ️ Instrucciones", "value": message.instructions[:1024]})
        if message.source_url:
            embed["url"] = message.source_url

        embed["footer"] = {"text": "ESPAlert — Alertas en tiempo real para España"}

        payload = {
            "username": "ESPAlert",
            "embeds": [embed],
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(target, json=payload)

            if resp.status_code in (200, 204):
                logger.info("Discord sent: %s", message.title[:50])
                return True

            logger.warning("Discord failed (%d): %s", resp.status_code, resp.text[:200])
            return False
