"""Prompt for naming a new theme from a representative feedback item."""


def build_theme_label_messages(text: str, category: str) -> list[dict]:
    """Build messages asking the LLM to name a theme for this feedback."""
    system = (
        "You group customer feedback into short, reusable themes. Given one "
        "feedback item and its category, propose a concise theme that "
        "similar future feedback could also belong to.\n\n"
        "Return ONLY JSON with these keys:\n"
        '  "label": a short theme name, 2-5 words, Title Case '
        '(e.g. "Upload Crashes", "Confusing Onboarding")\n'
        '  "keywords": 3-8 comma-separated keywords capturing the theme\n'
    )
    user = f"Category: {category}\nFeedback: {text}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
