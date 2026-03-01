"""Notification service — sends push notifications via Firebase Cloud Messaging."""

import logging
import json
from datetime import datetime, timezone
from typing import Optional

import asyncio

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
        """Lazy-init Firebase Admin SDK."""
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
            logger.warning(f"Firebase init failed (push disabled): {e}")

    async def notify_users(self, event: Event, affected_users: list[dict]):
        """
        Send push notifications to all affected users
        and publish the event to Redis for WebSocket broadcast.
        """
        # 1. Publish to Redis for real-time WebSocket clients
        await self._publish_to_redis(event)

        # 2. Send FCM push to each affected user
        if affected_users:
            self._init_firebase()
            await self._send_fcm_batch(event, affected_users)

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
            logger.error(f"Redis publish failed: {e}")

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
                batch_tokens = tokens[i:i+500]

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
                        "click_action": "FLUTTER_NOTIFICATION_CLICK",
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

                response = await asyncio.to_thread(
                    messaging.send_each_for_multicast, message
                )
                logger.info(
                    f"FCM batch: {response.success_count} sent, "
                    f"{response.failure_count} failed"
                )

        except ImportError:
            logger.warning("firebase_admin not available — push notifications disabled")
        except Exception as e:
            logger.error(f"FCM send failed: {e}")
