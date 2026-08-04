"""Group feedback into themes via vector similarity (no clustering).

For each feedback item: find the nearest existing theme. If it is within
THEME_SIMILARITY_THRESHOLD, join it; otherwise ask the LLM to name a new
theme, persist it to Postgres, and store its vector via pgvector.
"""

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.models.feedback import Feedback, Theme
from src.prompts.theme_label_prompt import build_theme_label_messages
from src.schemas.feedback import ThemeLabel
from src.services import vector_store
from src.services.openai_client import chat_json
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def assign_theme(db: Session, feedback: Feedback) -> Theme:
    """Assign `feedback` to an existing or new theme and return it."""
    match = vector_store.nearest_theme(feedback.text)
    if match and match["distance"] < settings.theme_similarity_threshold:
        theme = db.get(Theme, match["theme_id"])
        logger.info(
            "Feedback %s joined theme '%s' (distance=%.3f)",
            feedback.id, theme.label, match["distance"],
        )
    else:
        theme = _create_theme(db, feedback)
        logger.info(
            "Feedback %s started new theme '%s'", feedback.id, theme.label
        )

    feedback.theme_id = theme.id
    db.commit()
    return theme


def _create_theme(db: Session, feedback: Feedback) -> Theme:
    """Name a new theme via the LLM, persist it, index its vector."""
    messages = build_theme_label_messages(
        feedback.text, feedback.category or "other"
    )
    proposal = chat_json(
        messages,
        schema=ThemeLabel,
        model=settings.openai_classifier_model,
    )
    theme = Theme(label=proposal.label)
    db.add(theme)
    db.commit()
    db.refresh(theme)
    vector_store.add_theme(theme.id, theme.label, proposal.keywords)
    return theme
