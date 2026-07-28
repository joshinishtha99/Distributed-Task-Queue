"""Task handlers: the actual work each task_type performs."""

import asyncio
from typing import Any, Awaitable, Callable

Handler = Callable[[dict[str, Any]], Awaitable[None]]


async def send_email(payload: dict[str, Any]) -> None:
    to = payload.get("to", "unknown")
    print(f"        -> START email to {to}")
    await asyncio.sleep(3)  # simulate a slow network call
    print(f"        -> DONE  email to {to}")


HANDLERS: dict[str, Handler] = {
    "send_email": send_email,
}


def get_handler(task_type: str) -> Handler | None:
    return HANDLERS.get(task_type)
