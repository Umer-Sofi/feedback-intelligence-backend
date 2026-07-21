"""Prompt construction for the feedback classifier.

Builds the chat messages for a single classification call: a system prompt
that pins the taxonomy + JSON contract, a few-shot block, then the feedback.
"""

import json

from src.constants import CATEGORIES, SENTIMENTS

_SYSTEM_PROMPT = (
    "You are a precise customer-feedback classifier. Classify each item "
    "into exactly one category and one sentiment, and return ONLY a JSON "
    "object.\n\n"
    f"Allowed categories (choose exactly one): {', '.join(CATEGORIES)}.\n"
    f"Allowed sentiments (choose exactly one): {', '.join(SENTIMENTS)}.\n\n"
    "Return JSON with exactly these keys:\n"
    '  "category": one of the allowed categories\n'
    '  "sentiment": one of the allowed sentiments\n'
    '  "sentiment_score": float from -1.0 (very negative) to 1.0 '
    "(very positive)\n"
    '  "confidence": float from 0.0 to 1.0 (how certain you are)\n'
)

# Few-shot examples: (feedback text, expected JSON output).
_FEW_SHOT = [
    (
        "The app crashes every time I upload a photo.",
        {"category": "bug", "sentiment": "negative",
         "sentiment_score": -0.8, "confidence": 0.95},
    ),
    (
        "It would be great if you added a dark mode.",
        {"category": "feature_request", "sentiment": "neutral",
         "sentiment_score": 0.1, "confidence": 0.9},
    ),
    (
        "Your support team resolved my issue in minutes. Amazing!",
        {"category": "customer_support", "sentiment": "positive",
         "sentiment_score": 0.9, "confidence": 0.92},
    ),
    (
        "The subscription is way too expensive for what it offers.",
        {"category": "pricing", "sentiment": "negative",
         "sentiment_score": -0.6, "confidence": 0.88},
    ),
]


def build_classifier_messages(text: str) -> list[dict]:
    """Build the chat messages for classifying one feedback item."""
    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    for example_text, example_json in _FEW_SHOT:
        messages.append({"role": "user", "content": example_text})
        messages.append(
            {"role": "assistant", "content": json.dumps(example_json)}
        )
    messages.append({"role": "user", "content": text})
    return messages
