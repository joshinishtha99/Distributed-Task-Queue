"""Application configuration.

Loads settings from environment variables (and the project's .env file)
into a single, validated, typed object. Every other module imports
`settings` from here, so configuration has exactly one source of truth.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env by absolute path from THIS file's location, so the app and
# tools like Alembic work regardless of the current working directory.
#   this file: <root>/backend/app/core/config.py
#   parents:      [0]=core [1]=app [2]=backend [3]=<root>
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    # Application
    app_name: str = "distributed-task-queue"
    environment: str = "development"
    log_level: str = "INFO"

    # PostgreSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Worker
    worker_concurrency: int = 5

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
