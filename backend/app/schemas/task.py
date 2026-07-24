"""HTTP request/response shapes for tasks (separate from the DB model)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import TaskStatus


class TaskCreate(BaseModel):
    """What a client is allowed to send when creating a task."""

    task_type: str = Field(..., min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """What we return to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    task_type: str
    payload: dict[str, Any]
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
