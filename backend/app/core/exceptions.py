"""Domain exceptions, independent of HTTP."""

from uuid import UUID


class TaskNotFoundError(Exception):
    """Raised when a task ID does not exist."""

    def __init__(self, task_id: UUID) -> None:
        self.task_id = task_id
        super().__init__(f"Task {task_id} not found")
