"""Aggregate analytics over processed feedback (reads SQLite only)."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.feedback import Feedback, Theme


def category_counts(db: Session) -> dict:
    """Return {category: count} over processed feedback."""
    rows = db.execute(
        select(Feedback.category, func.count())
        .where(Feedback.processed.is_(True))
        .group_by(Feedback.category)
    ).all()
    return {category: count for category, count in rows if category}


def sentiment_distribution(db: Session) -> dict:
    """Return sentiment counts plus the average sentiment score."""
    rows = db.execute(
        select(Feedback.sentiment, func.count())
        .where(Feedback.processed.is_(True))
        .group_by(Feedback.sentiment)
    ).all()
    counts = {sentiment: count for sentiment, count in rows if sentiment}
    average = db.execute(
        select(func.avg(Feedback.sentiment_score))
        .where(Feedback.processed.is_(True))
    ).scalar()
    return {"counts": counts, "average_score": average}


def flagged_count(db: Session) -> int:
    """Number of processed items flagged for manual review."""
    return db.execute(
        select(func.count())
        .select_from(Feedback)
        .where(Feedback.flagged_for_review.is_(True))
    ).scalar_one()


def theme_trends(db: Session, weeks: int = 4) -> list[dict]:
    """Week-over-week feedback counts per theme for the last `weeks` weeks."""
    since = datetime.now(timezone.utc) - timedelta(weeks=weeks)
    rows = db.execute(
        select(Feedback.theme_id, Feedback.created_at)
        .where(Feedback.processed.is_(True))
        .where(Feedback.theme_id.is_not(None))
        .where(Feedback.created_at >= since)
    ).all()

    # Bucket counts by (theme_id, ISO year-week) in Python.
    buckets = defaultdict(lambda: defaultdict(int))
    for theme_id, created_at in rows:
        year, week, _ = created_at.isocalendar()
        buckets[theme_id][f"{year}-W{week:02d}"] += 1

    labels = dict(db.execute(select(Theme.id, Theme.label)).all())
    trends = []
    for theme_id, weekly in buckets.items():
        trends.append({
            "theme_id": theme_id,
            "label": labels.get(theme_id, "Unknown"),
            "weekly_counts": dict(sorted(weekly.items())),
            "total": sum(weekly.values()),
        })
    trends.sort(key=lambda t: t["total"], reverse=True)
    return trends


def overview(db: Session) -> dict:
    """Bundle the headline analytics for the dashboard and summary."""
    total = db.execute(
        select(func.count())
        .select_from(Feedback)
        .where(Feedback.processed.is_(True))
    ).scalar_one()
    return {
        "total_processed": total,
        "categories": category_counts(db),
        "sentiment": sentiment_distribution(db),
        "flagged_for_review": flagged_count(db),
        "themes": theme_trends(db),
    }
