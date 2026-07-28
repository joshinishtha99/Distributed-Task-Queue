"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.api.routes import dashboard, tasks
from app.core.config import settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.app_name} in {settings.environment} mode")
    # Start the Redis->WebSocket forwarder as a background task.
    listener = asyncio.create_task(dashboard.redis_event_listener())
    yield
    listener.cancel()
    await engine.dispose()
    print(f"Shutting down {settings.app_name}")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

    @app.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    app.include_router(tasks.router)
    @app.get("/dashboard", response_class=HTMLResponse, tags=["dashboard"])
    async def serve_dashboard() -> str:
        from pathlib import Path
        html = Path(__file__).parent / "static" / "dashboard.html"
        return html.read_text()

    app.include_router(dashboard.router)
    return app


app = create_app()
