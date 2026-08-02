"""
VisionX — WebSocket Live Feed
=================================
Real-time WebSocket streaming for live detection data.
"""

from __future__ import annotations

import time
from typing import Any

from loguru import logger


class ConnectionManager:
    """Manages active WebSocket connections."""

    def __init__(self):
        self._active: dict[str, Any] = {}  # connection_id -> websocket
        self._subscriptions: dict[str, set[str]] = {}  # channel -> {conn_ids}

        logger.info("WebSocket Connection Manager initialized")

    async def connect(self, connection_id: str, websocket: Any) -> None:
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self._active[connection_id] = websocket
        logger.debug(f"WebSocket connected: {connection_id}")

    def disconnect(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        self._active.pop(connection_id, None)

        # Remove from all subscriptions
        for subscribers in self._subscriptions.values():
            subscribers.discard(connection_id)

        logger.debug(f"WebSocket disconnected: {connection_id}")

    def subscribe(self, connection_id: str, channel: str) -> None:
        """Subscribe a connection to a channel."""
        if channel not in self._subscriptions:
            self._subscriptions[channel] = set()
        self._subscriptions[channel].add(connection_id)

    def unsubscribe(self, connection_id: str, channel: str) -> None:
        """Unsubscribe a connection from a channel."""
        if channel in self._subscriptions:
            self._subscriptions[channel].discard(connection_id)

    async def send_to(self, connection_id: str, data: dict) -> None:
        """Send data to a specific connection."""
        ws = self._active.get(connection_id)
        if ws:
            try:
                await ws.send_json(data)
            except Exception:
                self.disconnect(connection_id)

    async def broadcast(self, channel: str, data: dict) -> None:
        """
        Broadcast data to all subscribers of a channel.

        Iterates a snapshot of the subscriber set: awaiting inside the loop
        yields to the event loop, so a concurrent connect/disconnect would
        otherwise raise "Set changed size during iteration".
        """
        subscribers = tuple(self._subscriptions.get(channel, ()))
        disconnected = []

        for conn_id in subscribers:
            ws = self._active.get(conn_id)
            if ws:
                try:
                    await ws.send_json(data)
                except Exception:
                    disconnected.append(conn_id)

        # Cleanup disconnected
        for conn_id in disconnected:
            self.disconnect(conn_id)

    async def shutdown(self) -> None:
        """
        Close every active connection.

        Called on application shutdown so clients get a clean close frame and
        reconnect deliberately, rather than hanging until a TCP timeout.
        """
        for conn_id, ws in tuple(self._active.items()):
            try:
                await ws.close(code=1001)  # 1001 = going away
            except Exception:
                pass
            self.disconnect(conn_id)

        self._subscriptions.clear()
        logger.info("WebSocket manager shut down")

    async def broadcast_detection(
        self,
        source_id: str,
        detections: list[dict],
        fps: float,
        frame_id: int,
    ) -> None:
        """Broadcast detection results to live feed subscribers."""
        await self.broadcast(
            f"live:{source_id}",
            {
                "type": "detection",
                "source_id": source_id,
                "frame_id": frame_id,
                "fps": fps,
                "detections": detections,
                "timestamp": time.time(),
            },
        )

    async def broadcast_event(self, event: dict) -> None:
        """Broadcast an event to all event subscribers."""
        await self.broadcast("events", {
            "type": "event",
            **event,
        })

    @property
    def connection_count(self) -> int:
        return len(self._active)

    def get_stats(self) -> dict:
        return {
            "active_connections": len(self._active),
            "channels": {
                ch: len(subs)
                for ch, subs in self._subscriptions.items()
            },
        }


# Global connection manager
ws_manager = ConnectionManager()
