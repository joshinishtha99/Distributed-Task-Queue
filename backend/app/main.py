"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import tasks
from app.core.config import settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown hook."""
    print(f"Starting {settings.app_name} in {settings.environment} mode")
    yield
    await engine.dispose()
    print(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    app.include_router(tasks.router)
    return app


app = create_app()
