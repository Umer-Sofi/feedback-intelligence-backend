"""Add ownership + workflow columns to the existing feedback table.

create_all() only creates missing *tables*, not missing *columns*, so
adding fields to a table that already holds data needs explicit ALTERs.
Uses ADD COLUMN IF NOT EXISTS, so it is safe to run repeatedly.

Run from the backend/ directory:
    python -m scripts.migrate_feedback_columns
"""

from sqlalchemy import text

from src.database.database import engine

_STATEMENTS = [
    "ALTER TABLE feedback ADD COLUMN IF NOT EXISTS user_id INTEGER "
    "REFERENCES users(id)",
    "ALTER TABLE feedback ADD COLUMN IF NOT EXISTS status VARCHAR(20) "
    "DEFAULT 'open'",
    "ALTER TABLE feedback ADD COLUMN IF NOT EXISTS admin_reply TEXT",
    "ALTER TABLE feedback ADD COLUMN IF NOT EXISTS priority VARCHAR(10)",
]


def migrate() -> None:
    """Apply each ALTER statement in a single transaction."""
    with engine.begin() as conn:
        for statement in _STATEMENTS:
            conn.execute(text(statement))
    print("feedback table migrated (ownership + workflow columns).")


if __name__ == "__main__":
    migrate()
