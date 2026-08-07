"""Generate the weekly narrative summary, grounded in retrieved feedback."""

from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.prompts.summary_prompt import build_summary_messages
from src.services import analytics, retrieval
from src.services.openai_client import chat
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Queries used to pull representative grounding quotes across concerns.
_GROUNDING_QUERIES = [
    "most common complaints and problems",
    "feature requests and suggestions",
    "praise and positive feedback",
]

# Only recurring themes go into the summary prompt (drop one-off noise).
_MIN_THEME_TOTAL = 2
_MAX_SUMMARY_THEMES = 10


def _to_dt(d: date) -> datetime:
    """Midnight UTC at the start of date `d`."""
    return datetime(d.year, d.month, d.day, tzinfo=timezone.utc)


def generate_weekly_summary(
    db: Session, start: Optional[date] = None, days: int = 7
) -> dict:
    """Produce a narrative summary + the week's chartable stats.

    `start` -> the `days`-day week beginning on that date;
    omitted  -> the rolling last `days` days.

    Returns {summary, categories, sentiment, period}. Headline stats are
    scoped to the week; theme trends use a rolling window ending at the
    week's end; only the start date is shown.
    """
    if start:
        since = _to_dt(start)
        until = since + timedelta(days=days)
    else:
        until = datetime.now(timezone.utc)
        since = until - timedelta(days=days)
    from_d = since.date().isoformat()

    stats = analytics.overview(db, since=since, until=until)
    # Keep the week's category + sentiment breakdown for the UI charts
    # (before themes are trimmed for the prompt below).
    categories = stats["categories"]
    sentiment_counts = stats["sentiment"]["counts"]

    # No feedback in the window: say so plainly instead of grounding on
    # quotes from other weeks (retrieval isn't date-scoped). Skips the LLM.
    if stats["total_processed"] == 0:
        return {
            "summary": (
                f"No customer feedback was received for the week "
                f"starting {from_d}."
            ),
            "categories": {},
            "sentiment": {},
            "period": {"from": from_d, "count": 0},
        }

    # Keep only recurring themes (drop one-off singletons) and cap the count,
    # so the prompt highlights real trends instead of a wall of noise.
    top_themes = [
        t for t in stats["themes"] if t["total"] >= _MIN_THEME_TOTAL
    ][:_MAX_SUMMARY_THEMES]
    stats = {**stats, "themes": top_themes}

    quotes = []
    seen = set()
    for query in _GROUNDING_QUERIES:
        for item in retrieval.retrieve_relevant(db, query, n_results=3):
            if item["feedback_id"] not in seen:
                seen.add(item["feedback_id"])
                quotes.append(item)

    period = {
        "from": from_d,
        "count": stats["total_processed"],
    }
    messages = build_summary_messages(stats, quotes, period)
    summary = chat(messages, model=settings.openai_summary_model)
    logger.info("Generated weekly summary (%d chars)", len(summary))
    return {
        "summary": summary,
        "categories": categories,
        "sentiment": sentiment_counts,
        "period": period,
    }
