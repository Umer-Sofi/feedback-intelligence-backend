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


# Plain-string lists for injecting the allowed values into prompts.
CATEGORIES: list[str] = [c.value for c in Category]
SENTIMENTS: list[str] = [s.value for s in Sentiment]

# Numeric bounds referenced by schemas/validators (no magic numbers elsewhere).
SENTIMENT_SCORE_MIN = -1.0
SENTIMENT_SCORE_MAX = 1.0
CONFIDENCE_MIN = 0.0
CONFIDENCE_MAX = 1.0
