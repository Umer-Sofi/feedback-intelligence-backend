"""Load the processed feedback dataset into Postgres (+ pgvector).

Reads data/feedback.csv, inserts each row as an UNPROCESSED feedback record,
and (unless --skip-embeddings) stores its embedding vector on the row via
pgvector. This is the ONLY ingestion path — never an API call. Run manually
or via cron.
"""

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.database.database import SessionLocal
from src.database.init_db import init_db
from src.models.feedback import Feedback
from src.services import vector_store
from src.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_PATH = Path("data/feedback.csv")


def load_dataset(csv_path: Path, skip_embeddings: bool = False) -> int:
    """Insert feedback rows from `csv_path`; return the number inserted."""
    init_db()
    df = pd.read_csv(csv_path)
    inserted = 0
    db = SessionLocal()
    try:
        for _, row in df.iterrows():
            item = Feedback(
                source=str(row["source"]),
                text=str(row["text"]),
                created_at=datetime.fromisoformat(str(row["created_at"])),
                processed=False,
            )
            db.add(item)
            db.commit()
            db.refresh(item)
            if not skip_embeddings:
                vector_store.add_feedback(item.id, item.text)
            inserted += 1
    finally:
        db.close()
    logger.info("Loaded %d feedback records from %s", inserted, csv_path)
    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Load feedback dataset.")
    parser.add_argument(
        "--path", type=Path, default=DEFAULT_PATH,
        help="Processed CSV path (default: data/feedback.csv)",
    )
    parser.add_argument(
        "--skip-embeddings", action="store_true",
        help="Insert rows only; skip embeddings (offline / no API key).",
    )
    args = parser.parse_args()
    count = load_dataset(args.path, skip_embeddings=args.skip_embeddings)
    print(f"Inserted {count} records.")


if __name__ == "__main__":
    main()
