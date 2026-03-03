"""Servicio de notificaciones — envía notificaciones push vía Firebase Cloud Messaging."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from app.config import get_settings
from app.database import get_redis
from app.models.event import Event

logger = logging.getLogger(__name__)
settings = get_settings()

# Severidad → color de notificación + emoji
SEVERITY_DISPLAY = {
    "green": {"emoji": "🟢", "color": "#4CAF50"},
    "yellow": {"emoji": "🟡", "color": "#FFC107"},
    "orange": {"emoji": "🟠", "color": "#FF9800"},
    "red": {"emoji": "🔴", "color": "#F44336"},
}

# Tipo de evento → emoji
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
    Envía notificaciones push a usuarios afectados y publica
    en Redis pub/sub para clientes WebSocket en tiempo real.
    """

    def __init__(self):
        self._firebase_initialized = False

    def _init_firebase(self):
        """Inicialización perezosa del SDK Firebase Admin."""
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
            logger.warning("Inicialización Firebase falló (push desactivado): %s", e)

    async def notify_users(self, event: Event, affected_users: list[dict]):
        """
        Envía notificaciones push a todos los usuarios afectados
        y publica el evento en Redis para broadcast WebSocket.
        """
        # 1. Publicar en Redis para clientes WebSocket en tiempo real
        await self._publish_to_redis(event)

        # 2. Enviar push FCM a cada usuario afectado
        if affected_users:
            self._init_firebase()
            await self._send_fcm_batch(event, affected_users)

    async def _publish_to_redis(self, event: Event):
        """Publica nuevo evento en Redis pub/sub para broadcast WebSocket."""
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
            logger.error("Publicación Redis falló: %s", e)

    async def _send_fcm_batch(self, event: Event, users: list[dict]):
        """Envía notificaciones FCM a un lote de usuarios."""
        try:
            from firebase_admin import messaging

            severity_val = event.severity.value if event.severity else "green"
            type_val = event.event_type.value if event.event_type else "other"
            display = SEVERITY_DISPLAY.get(severity_val, SEVERITY_DISPLAY["green"])
            type_emoji = TYPE_EMOJI.get(type_val, "⚠️")

            title = f"{display['emoji']} {type_emoji} {event.title}"
            body = event.description[:200] if event.description else event.area_name or ""

            # Añadir cuenta regresiva si el evento aún no ha comenzado
            if event.effective and event.effective > datetime.now(timezone.utc):
                delta = event.effective - datetime.now(timezone.utc)
                minutes = int(delta.total_seconds() / 60)
                if minutes > 0:
                    body = f"⏱️ En {minutes} min — {body}"

            # Recopilar tokens FCM válidos
            tokens = [u["fcm_token"] for u in users if u.get("fcm_token")]

            if not tokens:
                return

            # Enviar multicast (hasta 500 tokens por llamada)
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

                response = await asyncio.to_thread(
                    messaging.send_each_for_multicast, message
                )
                logger.info(
                    "Lote FCM: %d enviados, %d fallidos",
                    response.success_count, response.failure_count,
                )

        except ImportError:
            logger.warning("firebase_admin no disponible — notificaciones push desactivadas")
        except Exception as e:
            logger.error("Envío FCM falló: %s", e)
