"""Business logic for tasks. Knows nothing about HTTP or SQL."""

from uuid import UUID

from app.core.exceptions import TaskNotFoundError
from app.models.task import Task
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskCreate


class TaskService:
    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    async def create_task(self, data: TaskCreate) -> Task:
        """Create a task. It starts life as PENDING."""
        return await self._repository.create(
            task_type=data.task_type,
            payload=data.payload,
        )

    async def get_task(self, task_id: UUID) -> Task:
        task = await self._repository.get_by_id(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
