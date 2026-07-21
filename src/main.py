"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.database.init_db import init_db
from src.routers import analytics, chat, feedback


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ensure database tables exist before serving requests."""
    init_db()
    yield


app = FastAPI(
    title="Feedback Intelligence API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", tags=["health"])
def health() -> dict:
    """Liveness check."""
    return {"status": "ok"}


app.include_router(feedback.router)
app.include_router(analytics.router)
app.include_router(chat.router)
