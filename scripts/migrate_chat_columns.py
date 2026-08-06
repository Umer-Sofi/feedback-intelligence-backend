"""Add the owner column to the existing chat_sessions table.

create_all() won't add a column to a table that already exists, so this
ALTER brings older databases up to date. Idempotent.

Run from the backend/ directory:
    python -m scripts.migrate_chat_columns
"""

from sqlalchemy import text

from src.database.database import engine

_STATEMENTS = [
    "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS user_id INTEGER "
    "REFERENCES users(id)",
]


def migrate() -> None:
    """Apply each ALTER statement in a single transaction."""
    with engine.begin() as conn:
        for statement in _STATEMENTS:
            conn.execute(text(statement))
    print("chat_sessions table migrated (owner column).")


if __name__ == "__main__":
    migrate()
