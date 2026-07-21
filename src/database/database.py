"""SQLAlchemy engine, session factory, and declarative base for SQLite."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import get_settings

settings = get_settings()

# SQLite requires check_same_thread=False so the connection can be reused
# across FastAPI's threadpool. Safe here: one local, single-writer file DB.
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    """Base class all ORM models inherit from."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yield a session, always close it afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
