"""Prompt construction for the feedback classifier.

Builds the chat messages for a single classification call: a system prompt
that pins the taxonomy + JSON contract, a few-shot block, then the feedback.
"""

import json

from src.constants import CATEGORIES, SENTIMENTS

_SYSTEM_PROMPT = (
    "You are a precise customer-feedback classifier. A submission may cover "
    "more than one topic. List EVERY applicable category, and give one "
    "overall sentiment for the whole submission. Return ONLY a JSON object."
    "\n\n"
    f"Allowed categories: {', '.join(CATEGORIES)}.\n"
    f"Allowed sentiments (choose exactly one): {', '.join(SENTIMENTS)}.\n\n"
    "Return JSON with exactly these keys:\n"
    '  "category": a JSON array of one or more allowed categories (list all '
    "topics present; use a single-element array for one topic)\n"
    '  "sentiment": one of the allowed sentiments (overall)\n'
    '  "sentiment_score": float from -1.0 (very negative) to 1.0 '
    "(very positive)\n"
    '  "confidence": float from 0.0 to 1.0 (how certain you are)\n'
)

# Few-shot examples: (feedback text, expected JSON output).
_FEW_SHOT = [
    (
        "The app crashes every time I upload a photo.",
        {"category": ["bug"], "sentiment": "negative",
         "sentiment_score": -0.8, "confidence": 0.95},
    ),
    (
        "It would be great if you added a dark mode.",
        {"category": ["feature_request"], "sentiment": "neutral",
         "sentiment_score": 0.1, "confidence": 0.9},
    ),
    (
        "The app keeps crashing on upload, and the new pricing is too high.",
        {"category": ["bug", "pricing"], "sentiment": "negative",
         "sentiment_score": -0.7, "confidence": 0.9},
    ),
    (
        "The subscription is way too expensive for what it offers.",
        {"category": ["pricing"], "sentiment": "negative",
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
