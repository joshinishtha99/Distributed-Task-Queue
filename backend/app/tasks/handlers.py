"""Task handlers: the actual work each task_type performs."""

import asyncio
from typing import Any, Awaitable, Callable

Handler = Callable[[dict[str, Any]], Awaitable[None]]


async def send_email(payload: dict[str, Any]) -> None:
    to = payload.get("to", "unknown")
    print(f"        -> START email to {to}")
    await asyncio.sleep(1)
    print(f"        -> DONE  email to {to}")


async def always_fails(payload: dict[str, Any]) -> None:
    """A handler that always raises — used to demonstrate retries and the DLQ."""
    print("        -> attempting a task that always fails")
    raise RuntimeError("simulated permanent failure")


HANDLERS: dict[str, Handler] = {
    "send_email": send_email,
    "always_fails": always_fails,
}


def get_handler(task_type: str) -> Handler | None:
    return HANDLERS.get(task_type)
