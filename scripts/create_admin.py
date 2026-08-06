"""Create (or reset) an admin user.

Usage, from the backend/ directory:
    python -m scripts.create_admin admin@example.com secretpass
"""

import sys
from datetime import datetime, timezone

from sqlalchemy import select

from src.core.security import hash_password
from src.database.database import SessionLocal
from src.database.init_db import init_db
from src.models.user import User


def create_admin(email: str, password: str) -> None:
    """Insert a new admin, or promote/reset the password if they exist."""
    init_db()
    db = SessionLocal()
    try:
        user = db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(password),
                role="admin",
                created_at=datetime.now(timezone.utc),
            )
            db.add(user)
        else:
            user.password_hash = hash_password(password)
            user.role = "admin"
        db.commit()
        print(f"Admin ready: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.create_admin <email> <password>")
        raise SystemExit(1)
    create_admin(sys.argv[1], sys.argv[2])
