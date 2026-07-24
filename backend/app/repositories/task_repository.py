"""All database access for tasks lives here — and nowhere else."""

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus


class TaskRepository:
    """Reads and writes Task rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, task_type: str, payload: dict[str, Any]) -> Task:
        task = Task(task_type=task_type, payload=payload, status=TaskStatus.PENDING)
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return task

    async def get_by_id(self, task_id: UUID) -> Task | None:
        return await self._session.get(Task, task_id)
