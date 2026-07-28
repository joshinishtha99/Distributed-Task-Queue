"""WebSocket endpoint + a Redis listener that forwards events to browsers."""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.queue.redis_client import get_redis
from app.websocket.events import EVENTS_CHANNEL
from app.websocket.manager import manager

router = APIRouter(tags=["dashboard"])


@router.websocket("/ws")
async def dashboard_ws(websocket: WebSocket) -> None:
    """A browser connects here to receive live task events."""
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from the browser; just keep the
            # connection open. This also detects disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def redis_event_listener() -> None:
    """Subscribe to Redis events and broadcast them to all dashboards."""
    redis = get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(EVENTS_CHANNEL)
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        import json
        await manager.broadcast(json.loads(message["data"]))
