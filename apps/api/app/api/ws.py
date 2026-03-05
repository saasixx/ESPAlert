"""WebSocket endpoint for real-time event streaming (with authentication)."""

import asyncio
import json
import logging

import jwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.config import get_settings
from app.database import get_redis

router = APIRouter(tags=["websocket"])
settings = get_settings()
logger = logging.getLogger(__name__)

# Maximum concurrent WebSocket connections
MAX_CONNECTIONS = 500


class ConnectionManager:
    """Manage active WebSocket connections with limits."""

    def __init__(self, max_connections: int = MAX_CONNECTIONS):
        self.active_connections: list[WebSocket] = []
        self.max_connections = max_connections

    async def connect(self, websocket: WebSocket) -> bool:
        if len(self.active_connections) >= self.max_connections:
            await websocket.close(code=1013, reason="Server overloaded")
            return False
        await websocket.accept()
        self.active_connections.append(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

    @property
    def count(self) -> int:
        return len(self.active_connections)


manager = ConnectionManager()


def _verify_ws_token(token: str) -> bool:
    """Verify JWT token for WebSocket authentication. Returns True if valid or if auth is optional."""
    if not token:
        return True  # Allow unauthenticated access for public event stream
    try:
        jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return True
    except jwt.InvalidTokenError:
        return False


@router.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket,
    token: str = Query(default=""),
):
    """
    Real-time event stream via WebSocket.
    Optional authentication with ?token=JWT_TOKEN parameter.
    """
    # Validate token if provided
    if token and not _verify_ws_token(token):
        await websocket.close(code=4001, reason="Token inválido")
        return

    if not await manager.connect(websocket):
        return

    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe("espalert:new_events")

    try:
        async def relay_redis():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await websocket.send_json(data)
                    except Exception as e:
                        logger.debug("WS relay error: %s", e)

        relay_task = asyncio.create_task(relay_redis())

        while True:
            try:
                await websocket.receive_text()
            except WebSocketDisconnect:
                break

    finally:
        relay_task.cancel()
        await pubsub.unsubscribe("espalert:new_events")
        manager.disconnect(websocket)
