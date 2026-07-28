"""The task queue: a thin wrapper over a Redis list.

We store only task IDs. The full task lives in PostgreSQL, so the queue
stays small and there is exactly one source of truth.
"""

from uuid import UUID

from app.queue.redis_client import get_redis

QUEUE_KEY = "taskqueue:pending"


class TaskQueue:
    """Push and pop task IDs."""

    def __init__(self) -> None:
        self._redis = get_redis()

    async def enqueue(self, task_id: UUID) -> None:
        """Add a task ID to the tail of the queue."""
        await self._redis.rpush(QUEUE_KEY, str(task_id))

    async def dequeue(self, timeout: int = 5) -> UUID | None:
        """Block until a task ID is available, or return None on timeout.

        BLPOP sleeps until something arrives instead of polling in a loop.
        """
        result = await self._redis.blpop(QUEUE_KEY, timeout=timeout)
        if result is None:
            return None
        _key, task_id = result
        return UUID(task_id)

    async def depth(self) -> int:
        """How many tasks are waiting."""
        return await self._redis.llen(QUEUE_KEY)
