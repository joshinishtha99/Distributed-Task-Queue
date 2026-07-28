"""Concurrent worker with retries, exponential backoff, DLQ, graceful shutdown."""

import asyncio
import signal

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.task import TaskStatus
from app.queue.backoff import compute_delay
from app.queue.task_queue import TaskQueue
from app.repositories.task_repository import TaskRepository
from app.tasks.handlers import get_handler


class Worker:
    def __init__(self) -> None:
        self._queue = TaskQueue()
        self._slots = asyncio.Semaphore(settings.worker_concurrency)
        self._in_flight: set[asyncio.Task] = set()
        self._shutting_down = False

    async def _retry_later(self, task_id, attempt: int) -> None:
        """Wait with backoff, then put the task back on the queue."""
        delay = compute_delay(attempt)
        print(f"[worker] retrying {task_id} in {delay:.1f}s (attempt {attempt})")
        await asyncio.sleep(delay)
        await self._queue.enqueue(task_id)

    async def _execute(self, task_id) -> None:
        async with AsyncSessionLocal() as session:
            repo = TaskRepository(session)
            task = await repo.get_by_id(task_id)
            if task is None:
                print(f"[worker] {task_id} not in DB, skipping")
                return

            await repo.mark_running_and_increment(task.id)
            await session.commit()
            await session.refresh(task)
            print(f"[worker] running {task.id} ({task.task_type}) attempt {task.attempts}/{task.max_attempts}")

            handler = get_handler(task.task_type)
            if handler is None:
                await repo.mark_dead(task.id, f"no handler for {task.task_type}")
                await session.commit()
                await self._queue.send_to_dlq(task.id)
                print(f"[worker] DEAD {task.id}: no handler")
                return

            try:
                await handler(task.payload)
                await repo.update_status(task.id, TaskStatus.COMPLETED)
                await session.commit()
                print(f"[worker] completed {task.id}")
            except Exception as exc:  # noqa: BLE001
                if task.attempts < task.max_attempts:
                    await repo.mark_failed(task.id, str(exc))
                    await session.commit()
                    print(f"[worker] FAILED {task.id}: {exc}")
                    await self._retry_later(task.id, task.attempts)
                else:
                    await repo.mark_dead(task.id, str(exc))
                    await session.commit()
                    await self._queue.send_to_dlq(task.id)
                    print(f"[worker] DEAD {task.id} after {task.attempts} attempts: {exc}")

    async def _run_tracked(self, task_id) -> None:
        try:
            await self._execute(task_id)
        finally:
            self._slots.release()

    def _install_signal_handlers(self, loop) -> None:
        def request_shutdown() -> None:
            if not self._shutting_down:
                print("\n[worker] shutdown requested, draining...")
            self._shutting_down = True
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, request_shutdown)

    async def run(self) -> None:
        loop = asyncio.get_running_loop()
        self._install_signal_handlers(loop)
        print(f"[worker] started, concurrency={settings.worker_concurrency}")
        while not self._shutting_down:
            await self._slots.acquire()
            if self._shutting_down:
                self._slots.release()
                break
            task_id = await self._queue.dequeue(timeout=2)
            if task_id is None:
                self._slots.release()
                continue
            coro = asyncio.create_task(self._run_tracked(task_id))
            self._in_flight.add(coro)
            coro.add_done_callback(self._in_flight.discard)
        if self._in_flight:
            print(f"[worker] waiting for {len(self._in_flight)} task(s)")
            await asyncio.gather(*self._in_flight, return_exceptions=True)
        print("[worker] shutdown complete")


if __name__ == "__main__":
    asyncio.run(Worker().run())
