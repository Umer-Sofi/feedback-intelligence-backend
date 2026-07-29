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
    db: Session,
    start: Optional[date] = None,
    end: Optional[date] = None,
    days: int = 7,
) -> str:
    """Produce a narrative summary for a date window (default: last 7 days).

    - start & end -> that inclusive date range
    - start only  -> the `days`-day week beginning on start
    - end only    -> the `days`-day week ending on end
    - neither     -> the rolling last `days` days

    Headline stats are scoped to the window; theme trends use a rolling
    window ending at the window's end; the date range is shown in the text.
    """
    if start and end:
        since = _to_dt(start)
        until = _to_dt(end) + timedelta(days=1)  # make end date inclusive
        from_d, to_d = start.isoformat(), end.isoformat()
    elif start:
        since = _to_dt(start)
        until = since + timedelta(days=days)
        from_d = start.isoformat()
        to_d = (until - timedelta(days=1)).date().isoformat()
    elif end:
        until = _to_dt(end) + timedelta(days=1)
        since = until - timedelta(days=days)
        from_d = since.date().isoformat()
        to_d = end.isoformat()
    else:
        until = datetime.now(timezone.utc)
        since = until - timedelta(days=days)
        from_d = since.date().isoformat()
        to_d = until.date().isoformat()

    stats = analytics.overview(db, since=since, until=until)

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
        "to": to_d,
        "count": stats["total_processed"],
    }
    messages = build_summary_messages(stats, quotes, period)
    summary = chat(messages, model=settings.openai_summary_model)
    logger.info("Generated weekly summary (%d chars)", len(summary))
    return summary
