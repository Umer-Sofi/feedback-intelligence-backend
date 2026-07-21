"""Classify a feedback item into category + sentiment via one LLM call."""

from src.core.config import get_settings
from src.prompts.classifier_prompt import build_classifier_messages
from src.schemas.feedback import ClassificationResult
from src.services.openai_client import chat_json
from src.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def classify(text: str) -> ClassificationResult:
    """Return the classification for a single piece of feedback text."""
    messages = build_classifier_messages(text)
    result = chat_json(
        messages,
        schema=ClassificationResult,
        model=settings.openai_classifier_model,
    )
    logger.info(
        "Classified: category=%s sentiment=%s confidence=%.2f",
        result.category,
        result.sentiment,
        result.confidence,
    )
    return result


def is_low_confidence(result: ClassificationResult) -> bool:
    """True if the result should be flagged for manual review."""
    return result.confidence < settings.low_confidence_threshold
