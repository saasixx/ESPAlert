"""Meshtastic mesh network gateway — bridges LoRa mesh to the ESPAlert backend."""

import asyncio
import logging
import json
from datetime import datetime, timezone
from typing import Optional

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Redis channels for mesh communication
MESH_CHANNEL_IN = "espalert:mesh:incoming"    # Messages FROM mesh
MESH_CHANNEL_OUT = "espalert:mesh:outgoing"   # Messages TO mesh
MESH_CHANNEL_NODES = "espalert:mesh:nodes"    # Node telemetry updates


class MeshMessage:
    """A message flowing through the Meshtastic mesh network."""

    def __init__(
        self,
        sender_id: str,
        sender_name: str,
        text: str,
        channel: int = 0,
        timestamp: Optional[datetime] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        snr: Optional[float] = None,
        rssi: Optional[int] = None,
        hop_count: Optional[int] = None,
    ):
        self.sender_id = sender_id
        self.sender_name = sender_name
        self.text = text
        self.channel = channel
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.lat = lat
        self.lon = lon
        self.snr = snr
        self.rssi = rssi
        self.hop_count = hop_count

    def to_dict(self) -> dict:
        return {
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "text": self.text,
            "channel": self.channel,
            "timestamp": self.timestamp.isoformat(),
            "lat": self.lat,
            "lon": self.lon,
            "snr": self.snr,
            "rssi": self.rssi,
            "hop_count": self.hop_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MeshMessage":
        return cls(
            sender_id=data.get("sender_id", ""),
            sender_name=data.get("sender_name", "Desconocido"),
            text=data.get("text", ""),
            channel=data.get("channel", 0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else None,
            lat=data.get("lat"),
            lon=data.get("lon"),
            snr=data.get("snr"),
            rssi=data.get("rssi"),
            hop_count=data.get("hop_count"),
        )


class MeshNode:
    """A Meshtastic node visible on the mesh network."""

    def __init__(
        self,
        node_id: str,
        long_name: str,
        short_name: str,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        altitude: Optional[int] = None,
        battery_level: Optional[int] = None,
        snr: Optional[float] = None,
        last_heard: Optional[datetime] = None,
    ):
        self.node_id = node_id
        self.long_name = long_name
        self.short_name = short_name
        self.lat = lat
        self.lon = lon
        self.altitude = altitude
        self.battery_level = battery_level
        self.snr = snr
        self.last_heard = last_heard or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "long_name": self.long_name,
            "short_name": self.short_name,
            "lat": self.lat,
            "lon": self.lon,
            "altitude": self.altitude,
            "battery_level": self.battery_level,
            "snr": self.snr,
            "last_heard": self.last_heard.isoformat() if self.last_heard else None,
        }


class MeshtasticGateway:
    """
    Backend gateway for Meshtastic mesh network.

    Connects to a Meshtastic node via serial/TCP and bridges messages
    to/from Redis pub/sub so the API and WebSocket can relay them.

    Run as a standalone process:
        python -m app.connectors.meshtastic_gw --port /dev/ttyUSB0
    """

    def __init__(self, connection_type: str = "serial", address: str = "/dev/ttyUSB0"):
        self.connection_type = connection_type
        self.address = address
        self.interface = None
        self.nodes: dict[str, MeshNode] = {}

    def connect(self):
        """Connect to the Meshtastic device."""
        try:
            import meshtastic
            import meshtastic.serial_interface
            import meshtastic.tcp_interface

            if self.connection_type == "serial":
                self.interface = meshtastic.serial_interface.SerialInterface(self.address)
            elif self.connection_type == "tcp":
                self.interface = meshtastic.tcp_interface.TCPInterface(self.address)
            else:
                raise ValueError(f"Unknown connection type: {self.connection_type}")

            logger.info(f"Connected to Meshtastic device via {self.connection_type}:{self.address}")

            # Subscribe to incoming messages
            from pubsub import pub

            pub.subscribe(self._on_receive, "meshtastic.receive.text")
            pub.subscribe(self._on_node_update, "meshtastic.node.updated")
            pub.subscribe(self._on_connection, "meshtastic.connection.established")

            # Load initial node list
            if self.interface.nodes:
                for node_id, node_info in self.interface.nodes.items():
                    self._update_node(node_id, node_info)

        except ImportError:
            logger.error(
                "meshtastic package not installed. "
                "Install with: pip install meshtastic"
            )
        except Exception as e:
            logger.exception(f"Failed to connect to Meshtastic device: {e}")

    def _on_receive(self, packet, interface):
        """Handle incoming mesh text message."""
        try:
            sender_id = packet.get("fromId", "")
            sender_name = packet.get("from", sender_id)

            # Look up sender name from nodes
            if sender_id in self.nodes:
                sender_name = self.nodes[sender_id].long_name

            decoded = packet.get("decoded", {})
            text = decoded.get("text", "")

            if not text:
                return

            # Extract position if available
            position = packet.get("position", {})
            lat = position.get("latitude")
            lon = position.get("longitude")

            msg = MeshMessage(
                sender_id=sender_id,
                sender_name=sender_name,
                text=text,
                channel=packet.get("channel", 0),
                snr=packet.get("snr"),
                rssi=packet.get("rssi"),
                hop_count=packet.get("hopStart", 0) - packet.get("hopLimit", 0),
                lat=lat,
                lon=lon,
            )

            # Publish to Redis
            asyncio.run(self._publish_message(msg))

            logger.info(f"Mesh RX: [{sender_name}] {text}")

        except Exception as e:
            logger.error(f"Error processing mesh message: {e}")

    def _on_node_update(self, node, interface):
        """Handle node telemetry update."""
        try:
            node_id = node.get("num", "")
            user = node.get("user", {})
            position = node.get("position", {})
            metrics = node.get("deviceMetrics", {})

            mesh_node = MeshNode(
                node_id=str(node_id),
                long_name=user.get("longName", f"Node-{node_id}"),
                short_name=user.get("shortName", "??"),
                lat=position.get("latitude"),
                lon=position.get("longitude"),
                altitude=position.get("altitude"),
                battery_level=metrics.get("batteryLevel"),
                snr=node.get("snr"),
            )

            self.nodes[str(node_id)] = mesh_node

            asyncio.run(self._publish_node_update(mesh_node))

        except Exception as e:
            logger.error(f"Error processing node update: {e}")

    def _on_connection(self, interface, topic=None):
        logger.info("Meshtastic connection established")

    async def _publish_message(self, msg: MeshMessage):
        """Publish received message to Redis.

        Uses a fresh connection (not the shared pool) because the gateway
        runs standalone and asyncio.run() creates a new event loop per call.
        """
        redis = aioredis.from_url(settings.REDIS_URL)
        try:
            await redis.publish(MESH_CHANNEL_IN, json.dumps(msg.to_dict()))
            # Also store in a list for history (keep last 500)
            await redis.lpush("espalert:mesh:history", json.dumps(msg.to_dict()))
            await redis.ltrim("espalert:mesh:history", 0, 499)
        finally:
            await redis.close()

    async def _publish_node_update(self, node: MeshNode):
        """Publish node update to Redis.

        Uses a fresh connection — same rationale as _publish_message.
        """
        redis = aioredis.from_url(settings.REDIS_URL)
        try:
            await redis.publish(MESH_CHANNEL_NODES, json.dumps(node.to_dict()))
            await redis.hset("espalert:mesh:active_nodes", node.node_id, json.dumps(node.to_dict()))
        finally:
            await redis.close()

    def send_message(self, text: str, channel: int = 0, destination: str = "^all"):
        """Send a text message to the mesh network."""
        if not self.interface:
            logger.error("Not connected to Meshtastic device")
            return False

        try:
            if destination == "^all":
                self.interface.sendText(text, channelIndex=channel)
            else:
                self.interface.sendText(text, destinationId=destination, channelIndex=channel)

            logger.info(f"Mesh TX: [{channel}] → {destination}: {text}")
            return True

        except Exception as e:
            logger.error(f"Failed to send mesh message: {e}")
            return False

    def send_alert_broadcast(self, event_title: str, severity: str, area: str):
        """Broadcast an alert summary to the mesh network."""
        severity_icons = {
            "red": "🔴",
            "orange": "🟠",
            "yellow": "🟡",
            "green": "🟢",
        }
        icon = severity_icons.get(severity, "⚠️")
        text = f"{icon} ALERTA: {event_title}\n📍 {area}"

        # Trim to 228 bytes (Meshtastic max message size)
        if len(text.encode("utf-8")) > 228:
            text = text[:220] + "..."

        return self.send_message(text)

    def get_nodes(self) -> list[dict]:
        """Get all known mesh nodes."""
        return [n.to_dict() for n in self.nodes.values()]

    def disconnect(self):
        """Close connection to Meshtastic device."""
        if self.interface:
            self.interface.close()
            logger.info("Meshtastic device disconnected")


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ESPAlert Meshtastic Gateway")
    parser.add_argument("--type", choices=["serial", "tcp"], default="serial")
    parser.add_argument("--address", default="/dev/ttyUSB0",
                        help="Serial port or TCP host:port")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    gateway = MeshtasticGateway(args.type, args.address)
    gateway.connect()

    logger.info("Gateway running. Press Ctrl+C to exit.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        gateway.disconnect()
