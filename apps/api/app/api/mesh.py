"""Mesh chat API — HTTP + WebSocket endpoints for Meshtastic communication (hardened)."""

import asyncio
import json
import logging
from datetime import datetime, timezone

import jwt
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

# Maximum message length for Meshtastic
MAX_MSG_LENGTH = 228


@router.get("/messages")
async def get_mesh_history(
    limit: int = Query(50, le=200, ge=1),
):
    """Get recent mesh message history (public, read-only)."""
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
    """Get known Meshtastic nodes (public, read-only)."""
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
    Enqueue a message to the mesh network. Requires authentication.
    Rate-limited to prevent spam.
    """
    # Sanitize input
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

    logger.info("Mesh message enqueued by user %s: %s...", user.id, clean_text[:50])
    return {"status": "enqueued", "message": message}


@router.websocket("/ws")
async def mesh_websocket(websocket: WebSocket):
    """
    Real-time WebSocket for mesh chat.
    Receives: incoming mesh messages + node updates.
    Sends: outgoing messages (requires authentication).

    Authentication is performed at connection time via the
    Authorization: Bearer <token> HTTP header sent during the WebSocket
    upgrade handshake. The connection is rejected with close code 4001
    if the token is missing or invalid.
    """
    # Authenticate at connection time using the Authorization header
    auth_header = websocket.headers.get("authorization", "")
    token = auth_header[7:] if auth_header.lower().startswith("bearer ") else ""

    if not token:
        await websocket.accept()
        await websocket.close(code=4001, reason="Token requerido")
        return

    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        authenticated_user = payload.get("sub")
    except jwt.InvalidTokenError:
        await websocket.accept()
        await websocket.close(code=4001, reason="Token inválido")
        return

    if not authenticated_user:
        await websocket.accept()
        await websocket.close(code=4001, reason="Token inválido")
        return

    await websocket.accept()

    from app.database import get_redis

    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(
        "espalert:mesh:incoming",
        "espalert:mesh:nodes",
    )

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

                if client_data.get("action") == "send":
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
