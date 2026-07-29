"""Aggregate analytics over processed feedback (reads the database only)."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.models.feedback import Feedback, Theme


def _in_window(stmt, since: Optional[datetime], until: Optional[datetime]):
    """Add created_at >= since and < until filters when they are given."""
    if since is not None:
        stmt = stmt.where(Feedback.created_at >= since)
    if until is not None:
        stmt = stmt.where(Feedback.created_at < until)
    return stmt


def category_counts(
    db: Session,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> dict:
    """Return {category: count} over processed feedback in the window."""
    stmt = _in_window(
        select(Feedback.category, func.count())
        .where(Feedback.processed.is_(True)),
        since, until,
    )
    rows = db.execute(stmt.group_by(Feedback.category)).all()
    return {category: count for category, count in rows if category}


def sentiment_distribution(
    db: Session,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> dict:
    """Return sentiment counts plus the average sentiment score."""
    stmt = _in_window(
        select(Feedback.sentiment, func.count())
        .where(Feedback.processed.is_(True)),
        since, until,
    )
    rows = db.execute(stmt.group_by(Feedback.sentiment)).all()
    counts = {sentiment: count for sentiment, count in rows if sentiment}

    avg_stmt = _in_window(
        select(func.avg(Feedback.sentiment_score))
        .where(Feedback.processed.is_(True)),
        since, until,
    )
    average = db.execute(avg_stmt).scalar()
    return {"counts": counts, "average_score": average}


def flagged_count(
    db: Session,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> int:
    """Number of items flagged for manual review in the window."""
    stmt = _in_window(
        select(func.count())
        .select_from(Feedback)
        .where(Feedback.flagged_for_review.is_(True)),
        since, until,
    )
    return db.execute(stmt).scalar_one()


def theme_trends(
    db: Session, weeks: int = 4, until: Optional[datetime] = None
) -> list[dict]:
    """Week-over-week counts per theme for the `weeks` weeks up to `until`."""
    end = until or datetime.now(timezone.utc)
    since = end - timedelta(weeks=weeks)
    rows = db.execute(
        _in_window(
            select(Feedback.theme_id, Feedback.created_at)
            .where(Feedback.processed.is_(True))
            .where(Feedback.theme_id.is_not(None)),
            since, end,
        )
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


def overview(
    db: Session,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> dict:
    """Bundle the headline analytics for the dashboard and summary.

    `since`/`until` scope the headline stats to a window (used by the weekly
    summary); left as None they cover all feedback (dashboard). Theme trends
    use a rolling window ending at `until` (or now) to show movement.
    """
    stmt = _in_window(
        select(func.count())
        .select_from(Feedback)
        .where(Feedback.processed.is_(True)),
        since, until,
    )
    total = db.execute(stmt).scalar_one()
    return {
        "total_processed": total,
        "categories": category_counts(db, since, until),
        "sentiment": sentiment_distribution(db, since, until),
        "flagged_for_review": flagged_count(db, since, until),
        "themes": theme_trends(db, until=until),
    }
