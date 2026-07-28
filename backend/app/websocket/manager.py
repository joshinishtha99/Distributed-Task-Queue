"""Tracks connected dashboard clients and broadcasts events to them all."""

import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Holds live WebSocket connections and fans out messages."""

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Send an event to every connected client; drop dead ones."""
        message = json.dumps(event, default=str)
        dead = set()
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001
                dead.add(ws)
        for ws in dead:
            self._connections.discard(ws)

    @property
    def count(self) -> int:
        return len(self._connections)


# A single shared manager for the whole app.
manager = ConnectionManager()
