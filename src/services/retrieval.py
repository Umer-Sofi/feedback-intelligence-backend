"""RAG retrieval: find feedback relevant to a query, enriched from SQLite."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.feedback import Feedback
from src.services import vector_store
from src.utils.logger import get_logger

logger = get_logger(__name__)


def retrieve_relevant(
    db: Session, query: str, n_results: int = 5
) -> list[dict]:
    """Return feedback most relevant to `query`, with category/sentiment.

    Vector search finds the items; SQLite supplies their structured fields
    so callers can cite and ground on real records.
    """
    hits = vector_store.search_feedback(query, n_results=n_results)
    if not hits:
        return []

    ids = [h["feedback_id"] for h in hits]
    rows = {
        row.id: row
        for row in db.execute(
            select(Feedback).where(Feedback.id.in_(ids))
        ).scalars()
    }

    results = []
    for hit in hits:
        row = rows.get(hit["feedback_id"])
        results.append({
            "feedback_id": hit["feedback_id"],
            "text": hit["text"],
            "distance": hit["distance"],
            "category": row.category if row else None,
            "sentiment": row.sentiment if row else None,
        })
    return results
