"""
Shared taxonomy constants used across prompts, schemas,
validation, and database models.
"""

from enum import Enum


class Category(str, Enum):
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    PRICING = "pricing"
    USABILITY = "usability"
    PERFORMANCE = "performance"
    CUSTOMER_SUPPORT = "customer_support"
    ONBOARDING = "onboarding"
    PRAISE = "praise"
    OTHER = "other"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class Status(str, Enum):
    """Lifecycle of a feedback item (set by an admin)."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class Priority(str, Enum):
    """Triage level derived from the AI's category + sentiment."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Plain-string lists for injecting the allowed values into prompts.
CATEGORIES: list[str] = [c.value for c in Category]
SENTIMENTS: list[str] = [s.value for s in Sentiment]
STATUSES: list[str] = [s.value for s in Status]

# Numeric bounds referenced by schemas/validators (no magic numbers elsewhere).
SENTIMENT_SCORE_MIN = -1.0
SENTIMENT_SCORE_MAX = 1.0
CONFIDENCE_MIN = 0.0
CONFIDENCE_MAX = 1.0
