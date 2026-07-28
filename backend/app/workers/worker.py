"""A concurrent worker with graceful shutdown.

- Runs up to WORKER_CONCURRENCY tasks at the same time (concurrency).
- On SIGTERM/SIGINT: stops pulling new tasks, lets in-flight tasks finish,
  then exits. No work is abandoned mid-flight.
"""

import asyncio
import signal

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.task import TaskStatus
from app.queue.task_queue import TaskQueue
from app.repositories.task_repository import TaskRepository
from app.tasks.handlers import get_handler


class Worker:
    """Pulls task IDs from Redis and runs them concurrently."""

    def __init__(self) -> None:
        self._queue = TaskQueue()
        # A semaphore caps how many tasks run at once. Acquiring it before
        # starting a task and releasing it after enforces the concurrency limit.
        self._slots = asyncio.Semaphore(settings.worker_concurrency)
        # Tracks currently-running task coroutines so shutdown can await them.
        self._in_flight: set[asyncio.Task] = set()
        # Flipped to True when a stop signal arrives.
        self._shutting_down = False

    async def _execute(self, task_id) -> None:
        """Load one task, run its handler, record the outcome."""
        async with AsyncSessionLocal() as session:
            repo = TaskRepository(session)
            task = await repo.get_by_id(task_id)
            if task is None:
                print(f"[worker] {task_id} not in DB, skipping")
                return

            print(f"[worker] running {task.id} ({task.task_type})")
            await repo.update_status(task.id, TaskStatus.RUNNING)
            await session.commit()

            handler = get_handler(task.task_type)
            if handler is None:
                await repo.update_status(task.id, TaskStatus.FAILED)
                await session.commit()
                print(f"[worker] no handler for {task.task_type}")
                return

            try:
                await handler(task.payload)
                await repo.update_status(task.id, TaskStatus.COMPLETED)
                await session.commit()
                print(f"[worker] completed {task.id}")
            except Exception as exc:  # noqa: BLE001
                await repo.update_status(task.id, TaskStatus.FAILED)
                await session.commit()
                print(f"[worker] FAILED {task.id}: {exc}")

    async def _run_tracked(self, task_id) -> None:
        """Wrap _execute so the semaphore slot is always released."""
        try:
            await self._execute(task_id)
        finally:
            self._slots.release()

    def _install_signal_handlers(self, loop: asyncio.AbstractEventLoop) -> None:
        def request_shutdown() -> None:
            if not self._shutting_down:
                print("\n[worker] shutdown requested, draining in-flight tasks...")
            self._shutting_down = True

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, request_shutdown)

    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        self._install_signal_handlers(loop)
        print(f"[worker] started, concurrency={settings.worker_concurrency}")

        while not self._shutting_down:
            # Reserve a slot before pulling work, so we never pull more than
            # we can run. This also naturally applies backpressure.
            await self._slots.acquire()

            if self._shutting_down:
                self._slots.release()
                break

            task_id = await self._queue.dequeue(timeout=2)
            if task_id is None:
                # No work right now; free the slot and loop.
                self._slots.release()
                continue

            coro = asyncio.create_task(self._run_tracked(task_id))
            self._in_flight.add(coro)
            coro.add_done_callback(self._in_flight.discard)

        # Drain: wait for everything still running to finish.
        if self._in_flight:
            print(f"[worker] waiting for {len(self._in_flight)} task(s) to finish")
            await asyncio.gather(*self._in_flight, return_exceptions=True)
        print("[worker] shutdown complete")


if __name__ == "__main__":
    asyncio.run(Worker().run())
