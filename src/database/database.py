"""SQLAlchemy engine, session factory, and declarative base for Postgres."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import get_settings

settings = get_settings()

# pool_pre_ping recycles dead connections (e.g. after the DB container
# restarts) so requests don't fail on a stale pooled connection.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
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
