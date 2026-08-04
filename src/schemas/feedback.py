"""Pydantic schemas for feedback classification and API responses."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from src.constants import (
    CONFIDENCE_MAX,
    CONFIDENCE_MIN,
    SENTIMENT_SCORE_MAX,
    SENTIMENT_SCORE_MIN,
    Category,
    Sentiment,
)


class FeedbackCreate(BaseModel):
    """Feedback submitted through the API by a user."""

    text: str = Field(min_length=1, max_length=5000)


class ClassificationResult(BaseModel):
    """Validated structured output from the classifier LLM call.

    `category` is a list so a single submission covering several topics can
    carry all applicable categories (stored comma-separated).
    """

    category: list[Category] = Field(min_length=1)
    sentiment: Sentiment
    sentiment_score: float = Field(
        ge=SENTIMENT_SCORE_MIN, le=SENTIMENT_SCORE_MAX
    )
    confidence: float = Field(ge=CONFIDENCE_MIN, le=CONFIDENCE_MAX)


class FeedbackOut(BaseModel):
    """A feedback record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    created_at: datetime
    processed: bool
    # Comma-separated categories (a feedback may span multiple topics).
    category: Optional[str] = None
    sentiment: Optional[Sentiment] = None
    sentiment_score: Optional[float] = None
    confidence: Optional[float] = None
    theme_id: Optional[int] = None


class ThemeLabel(BaseModel):
    """LLM-proposed name + keywords for a new theme."""

    label: str = Field(min_length=1, max_length=60)
    keywords: str = Field(min_length=1)
