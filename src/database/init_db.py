"""Create all database tables. Run once, or after changing any model."""

from sqlalchemy import text

from src.database.database import Base, engine

# These imports look "unused" but are REQUIRED: importing the model modules
# registers their classes on Base.metadata, so create_all knows about them.
from src.models import feedback as _feedback_models  # noqa: F401
from src.models import chat as _chat_models  # noqa: F401


def init_db() -> None:
    """Enable pgvector, then create every table on Base.metadata."""
    # The `vector` column type requires the pgvector extension to exist
    # before any table using it can be created.
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database initialized. Tables created.")
