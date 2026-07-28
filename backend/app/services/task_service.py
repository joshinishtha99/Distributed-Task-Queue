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
        """Persist a task as PENDING, then enqueue its id for a worker."""
        task = await self._repository.create(
            task_type=data.task_type,
            payload=data.payload,
        )
        # Persist first, enqueue second: the DB is the source of truth,
        # so a task must exist before a worker could try to load it.
        await self._queue.enqueue(task.id)
        return task

    async def get_task(self, task_id: UUID) -> Task:
        task = await self._repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
