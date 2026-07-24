"""Task HTTP endpoints. Translates HTTP <-> service calls, nothing more."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import TaskServiceDep
from app.core.exceptions import TaskNotFoundError
from app.schemas.task import TaskCreate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(data: TaskCreate, service: TaskServiceDep) -> TaskResponse:
    """Accept a task and persist it as PENDING."""
    task = await service.create_task(data)
    return TaskResponse.model_validate(task)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, service: TaskServiceDep) -> TaskResponse:
    """Fetch a task by id."""
    try:
        task = await service.get_task(task_id)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        ) from None
    return TaskResponse.model_validate(task)
