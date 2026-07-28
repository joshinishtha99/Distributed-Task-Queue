"""Cross-process event bus using Redis pub/sub.

The worker (a separate process) publishes task events here. The API
subscribes and forwards them to connected dashboards over WebSocket.
"""

import json
from typing import Any

from app.queue.redis_client import get_redis

EVENTS_CHANNEL = "taskqueue:events"


async def publish_event(event: dict[str, Any]) -> None:
    """Publish a task event for the dashboard to pick up."""
    redis = get_redis()
    await redis.publish(EVENTS_CHANNEL, json.dumps(event, default=str))
