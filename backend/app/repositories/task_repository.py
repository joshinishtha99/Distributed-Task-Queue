"""All database access for tasks lives here — and nowhere else."""

from typing import Any
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus


class TaskRepository:
    """Reads and writes Task rows."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        task_type: str,
        payload: dict[str, Any],
        idempotency_key: str | None = None,
        max_attempts: int = 3,
    ) -> Task:
        task = Task(
            task_type=task_type,
            payload=payload,
            status=TaskStatus.PENDING,
            idempotency_key=idempotency_key,
            max_attempts=max_attempts,
        )
        self._session.add(task)
        await self._session.flush()
        await self._session.refresh(task)
        return task

    async def get_by_id(self, task_id: UUID) -> Task | None:
        return await self._session.get(Task, task_id)

    async def get_by_idempotency_key(self, key: str) -> Task | None:
        result = await self._session.execute(
            select(Task).where(Task.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def update_status(self, task_id: UUID, status: TaskStatus) -> None:
        await self._session.execute(
            update(Task).where(Task.id == task_id).values(status=status)
        )

    async def mark_running_and_increment(self, task_id: UUID) -> None:
        """Set RUNNING and bump the attempt counter by one."""
        await self._session.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(status=TaskStatus.RUNNING, attempts=Task.attempts + 1)
        )

    async def mark_failed(self, task_id: UUID, error: str) -> None:
        await self._session.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(status=TaskStatus.FAILED, last_error=error[:1000])
        )

    async def mark_dead(self, task_id: UUID, error: str) -> None:
        await self._session.execute(
            update(Task)
            .where(Task.id == task_id)
            .values(status=TaskStatus.DEAD, last_error=error[:1000])
        )
