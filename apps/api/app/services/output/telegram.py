"""Telegram output connector — sends alerts to Telegram channels/groups/users."""

import logging

import httpx

from app.services.output.base import OutputConnector, OutputMessage

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class TelegramConnector(OutputConnector):
    """
    Send alerts via the Telegram Bot API.

    Target: Chat ID (e.g. "@my_channel", "-1001234567890", "123456789")
    """

    def __init__(self, bot_token: str):
        self._token = bot_token

    @property
    def name(self) -> str:
        return "telegram"

    async def send(self, message: OutputMessage, target: str) -> bool:
        url = f"{TELEGRAM_API}/bot{self._token}/sendMessage"
        payload = {
            "chat_id": target,
            "text": message.format_html(),
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload)

            if resp.status_code == 200:
                logger.info("Telegram sent to %s: %s", target, message.title[:50])
                return True

            logger.warning(
                "Telegram failed (%d) to %s: %s",
                resp.status_code, target, resp.text[:200],
            )
            return False
