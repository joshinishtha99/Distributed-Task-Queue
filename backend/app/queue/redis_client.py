"""Shared Redis connection factory."""

import redis.asyncio as redis

from app.core.config import settings

_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True,
    max_connections=20,
)


def get_redis() -> redis.Redis:
    """Return a Redis client backed by a shared connection pool."""
    return redis.Redis(connection_pool=_pool)
