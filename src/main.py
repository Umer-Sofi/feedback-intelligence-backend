"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database.init_db import init_db
from src.routers import analytics, auth, chat, feedback


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

# Allow the React dev server (Vite, port 5173) to call this API from a browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict:
    """Liveness check."""
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(feedback.router)
app.include_router(analytics.router)
app.include_router(chat.router)
