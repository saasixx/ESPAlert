"""Conector de salida Webhook genérico — envía alertas via HTTP POST."""

import logging
from datetime import datetime, timezone

import httpx

from app.services.output.base import OutputConnector, OutputMessage

logger = logging.getLogger(__name__)


class WebhookConnector(OutputConnector):
    """
    Envía alertas a cualquier endpoint HTTP como JSON.

    Target: URL completa del endpoint (https://example.com/webhook)
    """

    def __init__(self, secret: str = ""):
        self._secret = secret

    @property
    def name(self) -> str:
        return "webhook"

    async def send(self, message: OutputMessage, target: str) -> bool:
        payload = {
            "event_id": message.event_id,
            "title": message.title,
            "severity": message.severity,
            "event_type": message.event_type,
            "description": message.description,
            "instructions": message.instructions,
            "area_name": message.area_name,
            "source_url": message.source_url,
            "magnitude": message.magnitude,
            "depth_km": message.depth_km,
            "effective": message.effective.isoformat() if message.effective else None,
            "expires": message.expires.isoformat() if message.expires else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        headers = {"Content-Type": "application/json", "User-Agent": "ESPAlert/1.0"}
        if self._secret:
            import hashlib
            import hmac
            import json

            body = json.dumps(payload, sort_keys=True)
            sig = hmac.new(self._secret.encode(), body.encode(), hashlib.sha256).hexdigest()
            headers["X-ESPAlert-Signature"] = f"sha256={sig}"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(target, json=payload, headers=headers)

            if 200 <= resp.status_code < 300:
                logger.info("Webhook enviado a %s: %s", target[:50], message.title[:50])
                return True

            logger.warning("Webhook fallo (%d) → %s: %s", resp.status_code, target[:50], resp.text[:200])
            return False
