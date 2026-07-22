"""Vector storage + similarity search backed by Postgres + pgvector.

Embeddings live in the same Postgres tables as the structured data:
  - feedback.embedding  -> one vector per feedback item (powers RAG retrieval)
  - themes.embedding     -> one vector per named theme (powers theme matching)

Embeddings come from OpenAI (via openai_client.embed); pgvector does the
cosine-distance nearest-neighbor search. No clustering — grouping is
nearest-neighbor lookup. The public API is stable, so callers
(theme_aggregator, retrieval, pipeline, load_dataset) need no changes.
"""

from typing import Optional

from sqlalchemy import select

from src.database.database import SessionLocal
from src.models.feedback import Feedback, Theme
from src.services.openai_client import embed
from src.utils.logger import get_logger

logger = get_logger(__name__)


def add_feedback(feedback_id: int, text: str) -> None:
    """Embed a feedback item and store the vector on its row."""
    vector = embed([text])[0]
    db = SessionLocal()
    try:
        item = db.get(Feedback, feedback_id)
        if item is not None:
            item.embedding = vector
            db.commit()
    finally:
        db.close()


def add_theme(theme_id: int, label: str, keywords: str) -> None:
    """Embed a theme's keywords and store the vector on its row."""
    vector = embed([keywords])[0]
    db = SessionLocal()
    try:
        theme = db.get(Theme, theme_id)
        if theme is not None:
            theme.keywords = keywords
            theme.embedding = vector
            db.commit()
    finally:
        db.close()


def nearest_theme(text: str) -> Optional[dict]:
    """Return the closest existing theme to `text`, or None if none exist.

    Returns {"theme_id", "label", "distance"}; distance is cosine distance
    (0.0 = identical, 2.0 = opposite).
    """
    vector = embed([text])[0]
    db = SessionLocal()
    try:
        distance = Theme.embedding.cosine_distance(vector)
        row = db.execute(
            select(Theme, distance.label("distance"))
            .where(Theme.embedding.is_not(None))
            .order_by(distance)
            .limit(1)
        ).first()
        if row is None:
            return None
        theme, dist = row
        return {
            "theme_id": theme.id,
            "label": theme.label,
            "distance": dist,
        }
    finally:
        db.close()


def search_feedback(query: str, n_results: int = 5) -> list[dict]:
    """Return the feedback items most similar to `query` (for RAG)."""
    vector = embed([query])[0]
    db = SessionLocal()
    try:
        distance = Feedback.embedding.cosine_distance(vector)
        rows = db.execute(
            select(Feedback, distance.label("distance"))
            .where(Feedback.embedding.is_not(None))
            .order_by(distance)
            .limit(n_results)
        ).all()
        return [
            {"feedback_id": item.id, "text": item.text, "distance": dist}
            for item, dist in rows
        ]
    finally:
        db.close()
