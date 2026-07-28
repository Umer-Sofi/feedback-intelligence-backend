"""Processing pipeline: classify + theme all unprocessed feedback.

A plain callable, triggered manually or by external cron — NOT an in-process
scheduler and NOT run on API startup. For each unprocessed feedback row it:
  1. classifies category + sentiment (services/classifier),
  2. writes results back and flags low-confidence items,
  3. assigns a theme via vector similarity (services/theme_aggregator).
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.database import SessionLocal
from src.models.feedback import Feedback
from src.services import classifier, theme_aggregator, vector_store
from src.utils.logger import get_logger

logger = get_logger(__name__)


def process_feedback_item(db: Session, item: Feedback) -> None:
    """Classify, persist, flag, and theme a single feedback item."""
    result = classifier.classify(item.text)
    item.category = result.category.value
    item.sentiment = result.sentiment.value
    item.sentiment_score = result.sentiment_score
    item.confidence = result.confidence
    item.flagged_for_review = classifier.is_low_confidence(result)
    item.processed = True
    db.commit()

    # Ensure the item's chunks + embeddings exist for RAG (load may skip them).
    vector_store.add_feedback(item.id, item.text)
    theme_aggregator.assign_theme(db, item)


def run_pipeline(
    db: Optional[Session] = None, limit: Optional[int] = None
) -> dict:
    """Process all unprocessed feedback; return a small run summary."""
    own_session = db is None
    if own_session:
        db = SessionLocal()
    processed = 0
    failed = 0
    try:
        stmt = select(Feedback).where(Feedback.processed.is_(False))
        if limit:
            stmt = stmt.limit(limit)
        items = list(db.execute(stmt).scalars())
        logger.info("Pipeline start: %d unprocessed items", len(items))
        for item in items:
            try:
                process_feedback_item(db, item)
                processed += 1
            except Exception as exc:
                db.rollback()
                failed += 1
                logger.exception("Failed on feedback %s: %s", item.id, exc)
    finally:
        if own_session:
            db.close()
    summary = {"processed": processed, "failed": failed}
    logger.info("Pipeline done: %s", summary)
    return summary


if __name__ == "__main__":
    print(run_pipeline())
