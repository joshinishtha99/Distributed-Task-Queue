"""Dependency injection wiring: session -> repository -> service."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.queue.task_queue import TaskQueue
from app.repositories.task_repository import TaskRepository
from app.services.task_service import TaskService


def get_task_repository(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TaskRepository:
    return TaskRepository(session)


def get_task_queue() -> TaskQueue:
    return TaskQueue()


def get_task_service(
    repository: Annotated[TaskRepository, Depends(get_task_repository)],
    queue: Annotated[TaskQueue, Depends(get_task_queue)],
) -> TaskService:
    return TaskService(repository, queue)


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
