"""API de chat Mesh — endpoints HTTP + WebSocket para comunicación Meshtastic (endurecido)."""

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.auth import get_current_user
from app.config import get_settings
from app.models.user import User

router = APIRouter(prefix="/mesh", tags=["meshtastic"])
settings = get_settings()
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, storage_uri=settings.REDIS_URL)

# Longitud máxima de mensaje para Meshtastic
MAX_MSG_LENGTH = 228


@router.get("/messages")
async def get_mesh_history(
    limit: int = Query(50, le=200, ge=1),
):
    """Obtiene el historial de mensajes mesh recientes (público, solo lectura)."""
    from app.database import get_redis
    redis = get_redis()
    raw = await redis.lrange("espalert:mesh:history", 0, limit - 1)
    messages = []
    for item in raw:
        try:
            messages.append(json.loads(item))
        except json.JSONDecodeError:
            pass

    return {"messages": messages}


@router.get("/nodes")
async def get_mesh_nodes():
    """Obtiene los nodos Meshtastic conocidos (público, solo lectura)."""
    from app.database import get_redis
    redis = get_redis()
    raw = await redis.hgetall("espalert:mesh:active_nodes")
    nodes = []
    for node_id, data in raw.items():
        try:
            nodes.append(json.loads(data))
        except json.JSONDecodeError:
            pass

    nodes.sort(key=lambda n: n.get("last_heard", ""), reverse=True)
    return {"nodes": nodes, "count": len(nodes)}


@router.post("/send")
@limiter.limit(settings.RATE_LIMIT_MESH_SEND)
async def send_mesh_message(
    request: Request,
    text: str = Query(..., max_length=MAX_MSG_LENGTH),
    channel: int = Query(0, ge=0, le=7),
    destination: str = Query("^all", max_length=20),
    user: User = Depends(get_current_user),  # Auth required
):
    """
    Encola un mensaje hacia la red mesh. Requiere autenticación.
    Limitado por tasa para prevenir spam.
    """
    # Sanitizar entrada
    clean_text = text.strip()
    if not clean_text:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")

    from app.database import get_redis
    redis = get_redis()
    message = {
        "text": clean_text[:MAX_MSG_LENGTH],
        "channel": channel,
        "destination": destination,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "espalert_api",
        "user_id": str(user.id),
        "user_name": user.display_name or f"User-{str(user.id)[:6]}",
    }

    await redis.publish("espalert:mesh:outgoing", json.dumps(message))

    logger.info("Mensaje mesh encolado por usuario %s: %s...", user.id, clean_text[:50])
    return {"status": "encolado", "message": message}


@router.websocket("/ws")
async def mesh_websocket(websocket: WebSocket):
    """
    WebSocket en tiempo real para chat mesh.
    Recibe: mensajes mesh entrantes + actualizaciones de nodos.
    Envía: mensajes salientes (requiere token auth en el primer mensaje).
    """
    await websocket.accept()

    from app.database import get_redis
    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(
        "espalert:mesh:incoming",
        "espalert:mesh:nodes",
    )

    import asyncio
    import jwt as pyjwt

    authenticated_user = None  # Rastrear si el cliente WS se ha autenticado

    try:
        async def relay_from_mesh():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"]
                    data = json.loads(message["data"])
                    if isinstance(channel, bytes):
                        channel = channel.decode()
                    msg_type = "message" if "incoming" in channel else "node_update"
                    await websocket.send_json({"type": msg_type, "data": data})

        relay_task = asyncio.create_task(relay_from_mesh())

        while True:
            try:
                client_data = await websocket.receive_json()

                # Manejar mensaje de autenticación (debe autenticarse antes de enviar)
                if client_data.get("action") == "auth":
                    token = client_data.get("token", "")
                    try:
                        payload = pyjwt.decode(
                            token, settings.JWT_SECRET,
                            algorithms=[settings.JWT_ALGORITHM]
                        )
                        authenticated_user = payload.get("sub")
                        await websocket.send_json({"type": "auth", "status": "ok"})
                    except pyjwt.InvalidTokenError:
                        await websocket.send_json({"type": "auth", "status": "error", "detail": "Token inválido"})

                elif client_data.get("action") == "send":
                    # Requiere autenticación para enviar mensajes
                    if not authenticated_user:
                        await websocket.send_json({
                            "type": "error",
                            "detail": "Authenticate first: {\"action\": \"auth\", \"token\": \"JWT\"}"
                        })
                        continue

                    text = client_data.get("text", "").strip()
                    if text and len(text) <= MAX_MSG_LENGTH:
                        outgoing = {
                            "text": text,
                            "channel": min(client_data.get("channel", 0), 7),
                            "destination": client_data.get("destination", "^all")[:20],
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "source": "espalert_app",
                            "user_id": authenticated_user,
                        }
                        await redis.publish("espalert:mesh:outgoing", json.dumps(outgoing))

            except WebSocketDisconnect:
                break

    finally:
        relay_task.cancel()
        await pubsub.unsubscribe()
