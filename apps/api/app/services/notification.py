"""Notification service — sends push notifications via Firebase Cloud Messaging."""

import asyncio
import json
import logging
import hmac
import hashlib
from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.database import get_redis
from app.models.event import Event

logger = logging.getLogger(__name__)
settings = get_settings()

# Severity → notification color + emoji
SEVERITY_DISPLAY = {
    "green": {"emoji": "🟢", "color": "#4CAF50"},
    "yellow": {"emoji": "🟡", "color": "#FFC107"},
    "orange": {"emoji": "🟠", "color": "#FF9800"},
    "red": {"emoji": "🔴", "color": "#F44336"},
}

# Event type → emoji
TYPE_EMOJI = {
    "wind": "💨",
    "rain": "🌧️",
    "storm": "⛈️",
    "snow": "❄️",
    "ice": "🧊",
    "fog": "🌫️",
    "heat": "🌡️",
    "cold": "🥶",
    "uv": "☀️",
    "fire_risk": "🔥",
    "coastal": "🌊",
    "wave": "🌊",
    "tide": "🌊",
    "earthquake": "📳",
    "tsunami": "🌊",
    "traffic_accident": "🚗",
    "traffic_closure": "🚧",
    "traffic_works": "🔧",
    "traffic_jam": "🐌",
    "civil_protection": "🚨",
}


class NotificationService:
    """
    Sends push notifications to affected users and publishes
    to Redis pub/sub for real-time WebSocket clients.
    """

    def __init__(self):
        self._firebase_initialized = False

    def _init_firebase(self):
        """Lazy initialization of the Firebase Admin SDK."""
        if self._firebase_initialized:
            return
        try:
            import firebase_admin
            from firebase_admin import credentials

            if not firebase_admin._apps:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred)

            self._firebase_initialized = True
        except Exception as e:
            logger.warning("Firebase initialization failed (push disabled): %s", e)

    async def notify_users(self, event: Event, affected_users: list[dict]):
        """
        Send push notifications to all affected users
        and publish the event on Redis for WebSocket broadcast.
        """
        # 1. Publish to Redis for real-time WebSocket clients
        await self._publish_to_redis(event)

        # 2. Send FCM push to each affected user
        if affected_users:
            self._init_firebase()
            await self._send_fcm_batch(event, affected_users)

        # 3. Trigger webhooks and telegram if configured
        await self._dispatch_webhook(event)
        await self._send_telegram_batch(event, affected_users)

    async def _publish_to_redis(self, event: Event):
        """Publish new event to Redis pub/sub for WebSocket broadcast."""
        try:
            redis = get_redis()

            severity_val = event.severity.value if event.severity else "green"
            type_val = event.event_type.value if event.event_type else "other"

            message = {
                "id": str(event.id),
                "source": event.source.value if event.source else "",
                "event_type": type_val,
                "severity": severity_val,
                "title": event.title,
                "area_name": event.area_name,
                "effective": event.effective.isoformat() if event.effective else None,
                "expires": event.expires.isoformat() if event.expires else None,
                "magnitude": event.magnitude,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await redis.publish("espalert:new_events", json.dumps(message))

        except Exception as e:
            logger.error("Redis publish failed: %s", e)

    async def _send_fcm_batch(self, event: Event, users: list[dict]):
        """Send FCM notifications to a batch of users."""
        try:
            from firebase_admin import messaging

            severity_val = event.severity.value if event.severity else "green"
            type_val = event.event_type.value if event.event_type else "other"
            display = SEVERITY_DISPLAY.get(severity_val, SEVERITY_DISPLAY["green"])
            type_emoji = TYPE_EMOJI.get(type_val, "⚠️")

            title = f"{display['emoji']} {type_emoji} {event.title}"
            body = event.description[:200] if event.description else event.area_name or ""

            # Add countdown if event hasn't started yet
            if event.effective and event.effective > datetime.now(timezone.utc):
                delta = event.effective - datetime.now(timezone.utc)
                minutes = int(delta.total_seconds() / 60)
                if minutes > 0:
                    body = f"⏱️ En {minutes} min — {body}"

            # Collect valid FCM tokens
            tokens = [u["fcm_token"] for u in users if u.get("fcm_token")]

            if not tokens:
                return

            # Send multicast (up to 500 tokens per call)
            for i in range(0, len(tokens), 500):
                batch_tokens = tokens[i : i + 500]

                message = messaging.MulticastMessage(
                    tokens=batch_tokens,
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    data={
                        "event_id": str(event.id),
                        "event_type": type_val,
                        "severity": severity_val,
                        "source": event.source.value if event.source else "",
                        "click_action": "OPEN_WEB_ALERT",
                    },
                    android=messaging.AndroidConfig(
                        priority="high",
                        notification=messaging.AndroidNotification(
                            color=display["color"],
                            channel_id=f"espalert_{severity_val}",
                            sound="default" if severity_val in ("orange", "red") else None,
                        ),
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                sound="default" if severity_val in ("orange", "red") else None,
                                badge=1,
                            ),
                        ),
                    ),
                )

                response = await asyncio.to_thread(messaging.send_each_for_multicast, message)
                logger.info(
                    "FCM batch: %d sent, %d failed",
                    response.success_count,
                    response.failure_count,
                )

        except ImportError:
            logger.warning("firebase_admin not available — push notifications disabled")
        except Exception as e:
            logger.error("FCM send failed: %s", e)

    async def _send_telegram_batch(self, event: Event, users: list[dict]):
        """Send Telegram chat messages to a batch of affected users."""
        if not settings.TELEGRAM_BOT_TOKEN:
            return

        chat_ids = [u["telegram_chat_id"] for u in users if u.get("telegram_chat_id")]
        # Also include backward compatibility if email was overloaded or needed mapping
        if not chat_ids:
            return

        severity_val = event.severity.value if event.severity else "green"
        type_val = event.event_type.value if event.event_type else "other"
        display = SEVERITY_DISPLAY.get(severity_val, SEVERITY_DISPLAY["green"])
        type_emoji = TYPE_EMOJI.get(type_val, "⚠️")
        title = f"{display['emoji']} {type_emoji} *Alerta: {event.title}*"
        body = f"Nueva alerta en su zona de interés:\\n\\n*Severidad:* {severity_val.upper()}\\n*Tipo:* {type_val.upper()}\\n\\n*Descripción:*\\n{event.description or ''}"

        message_text = f"{title}\\n\\n{body}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                for chat_id in chat_ids:
                    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
                    payload = {
                        "chat_id": chat_id,
                        "text": message_text,
                        "parse_mode": "Markdown",
                    }
                    resp = await client.post(url, json=payload)
                    if resp.status_code != 200:
                        logger.warning("Telegram send failed for chat %s: %s", chat_id, resp.text)
            logger.info("Telegram batch sent: %d users", len(chat_ids))
        except Exception as e:
            logger.error("Telegram batch failed: %s", e)

    async def _dispatch_webhook(self, event: Event):
        """Dispatch event to configured webhook via POST if a URL is registered."""
        # For a full implementation this would query a webhooks table,
        # but for v0.2.0 we support a global webhook configured via ENV var.
        webhook_url = getattr(settings, "GLOBAL_WEBHOOK_URL", None)
        if not webhook_url:
            return

        payload = {
            "id": str(event.id),
            "source": event.source.value if event.source else "",
            "event_type": event.event_type.value if event.event_type else "other",
            "severity": event.severity.value if event.severity else "green",
            "title": event.title,
            "description": event.description,
            "area_name": event.area_name,
            "effective": event.effective.isoformat() if event.effective else None,
            "expires": event.expires.isoformat() if event.expires else None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        json_payload = json.dumps(payload)

        headers = {"Content-Type": "application/json"}
        if settings.WEBHOOK_SECRET:
            signature = hmac.new(settings.WEBHOOK_SECRET.encode(), json_payload.encode(), hashlib.sha256).hexdigest()
            headers["X-ESPAlert-Signature"] = f"sha256={signature}"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(webhook_url, content=json_payload, headers=headers)
                resp.raise_for_status()
                logger.debug("Webhook dispatched successfully: %s", resp.status_code)
        except Exception as e:
            logger.error("Webhook dispatch failed: %s", e)
