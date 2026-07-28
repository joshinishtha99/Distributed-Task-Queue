"""Task handlers: the actual work each task_type performs."""

import asyncio
from typing import Any, Awaitable, Callable

Handler = Callable[[dict[str, Any]], Awaitable[None]]


async def send_email(payload: dict[str, Any]) -> None:
    to = payload.get("to", "unknown")
    print(f"        -> START email to {to}")
    await asyncio.sleep(3)
    print(f"        -> DONE  email to {to}")


async def always_fails(payload: dict[str, Any]) -> None:
    print("        -> attempting a task that always fails")
    raise RuntimeError("simulated permanent failure")


async def benchmark(payload: dict[str, Any]) -> None:
    """A short fixed-work task for the scaling benchmark."""
    await asyncio.sleep(0.3)


HANDLERS: dict[str, Handler] = {
    "send_email": send_email,
    "always_fails": always_fails,
    "benchmark": benchmark,
}


def get_handler(task_type: str) -> Handler | None:
    return HANDLERS.get(task_type)
