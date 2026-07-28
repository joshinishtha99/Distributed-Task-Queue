"""Measure task-queue throughput.

Enqueues N benchmark tasks, waits until all complete, prints tasks/sec.
Run with different worker counts to see horizontal scaling.

Usage: python scripts/benchmark.py [N]
"""

import asyncio
import sys
import time

import httpx
from sqlalchemy import func, select

sys.path.insert(0, ".")
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.models.task import Task, TaskStatus  # noqa: E402

API = "http://localhost:8000"


async def count_completed(since) -> int:
    async with AsyncSessionLocal() as s:
        result = await s.execute(
            select(func.count())
            .select_from(Task)
            .where(Task.task_type == "benchmark")
            .where(Task.status == TaskStatus.COMPLETED)
            .where(Task.created_at >= since)
        )
        return result.scalar_one()


async def main(n: int) -> None:
    since = None
    async with AsyncSessionLocal() as s:
        since = (await s.execute(select(func.now()))).scalar_one()

    print(f"Enqueuing {n} benchmark tasks...")
    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        await asyncio.gather(*[
            client.post(f"{API}/tasks", json={"task_type": "benchmark", "payload": {}})
            for _ in range(n)
        ])

    print("Waiting for completion...")
    while await count_completed(since) < n:
        await asyncio.sleep(0.2)

    elapsed = time.perf_counter() - start
    print(f"\n  {n} tasks in {elapsed:.2f}s  =  {n / elapsed:.1f} tasks/sec")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    asyncio.run(main(n))
