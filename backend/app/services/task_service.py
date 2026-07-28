"""Business logic for tasks. Knows nothing about HTTP or SQL."""

from uuid import UUID

from app.core.exceptions import TaskNotFoundError
from app.models.task import Task
from app.queue.task_queue import TaskQueue
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate


class TaskService:
    def __init__(self, repository: TaskRepository, queue: TaskQueue) -> None:
        self._repository = repository
        self._queue = queue

    async def create_task(self, data: TaskCreate) -> Task:
        """Create a task, or return the existing one if the key was seen before."""
        if data.idempotency_key is not None:
            existing = await self._repository.get_by_idempotency_key(
                data.idempotency_key
            )
            if existing is not None:
                # Same key seen before: return the original, don't create or enqueue.
                return existing

        task = await self._repository.create(
            task_type=data.task_type,
            payload=data.payload,
            idempotency_key=data.idempotency_key,
        )
        await self._queue.enqueue(task.id)
        return task

    async def get_task(self, task_id: UUID) -> Task:
        task = await self._repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
