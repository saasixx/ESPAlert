"""Conector de salida Telegram — envía alertas a canales/grupos/usuarios de Telegram."""

import logging

import httpx

from app.services.output.base import OutputConnector, OutputMessage

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org"


class TelegramConnector(OutputConnector):
    """
    Envía alertas mediante la API de bots de Telegram.

    Target: ID de chat (e.g. "@mi_canal", "-1001234567890", "123456789")
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
                logger.info("Telegram enviado a %s: %s", target, message.title[:50])
                return True

            logger.warning(
                "Telegram fallo (%d) a %s: %s",
                resp.status_code, target, resp.text[:200],
            )
            return False
