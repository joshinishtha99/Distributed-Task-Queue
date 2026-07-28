"""The task queue: thin wrappers over Redis lists.

Store only task IDs. Full task lives in PostgreSQL — one source of truth.
"""

from uuid import UUID

from app.queue.redis_client import get_redis

QUEUE_KEY = "taskqueue:pending"
DLQ_KEY = "taskqueue:dead"


class TaskQueue:
    def __init__(self) -> None:
        self._redis = get_redis()

    async def enqueue(self, task_id: UUID) -> None:
        await self._redis.rpush(QUEUE_KEY, str(task_id))

    async def dequeue(self, timeout: int = 5) -> UUID | None:
        result = await self._redis.blpop(QUEUE_KEY, timeout=timeout)
        if result is None:
            return None
        _key, task_id = result
        return UUID(task_id)

    async def send_to_dlq(self, task_id: UUID) -> None:
        """Move a permanently-failed task to the dead-letter list."""
        await self._redis.rpush(DLQ_KEY, str(task_id))

    async def depth(self) -> int:
        return await self._redis.llen(QUEUE_KEY)

    async def dlq_depth(self) -> int:
        return await self._redis.llen(DLQ_KEY)
