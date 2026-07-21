"""Generate the weekly narrative summary, grounded in retrieved feedback."""

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


def generate_weekly_summary(db: Session) -> str:
    """Produce a narrative summary from aggregated stats + RAG quotes."""
    stats = analytics.overview(db)

    quotes = []
    seen = set()
    for query in _GROUNDING_QUERIES:
        for item in retrieval.retrieve_relevant(db, query, n_results=3):
            if item["feedback_id"] not in seen:
                seen.add(item["feedback_id"])
                quotes.append(item)

    messages = build_summary_messages(stats, quotes)
    summary = chat(messages, model=settings.openai_summary_model)
    logger.info("Generated weekly summary (%d chars)", len(summary))
    return summary
