"""Prompt for rewriting a follow-up question into a standalone query."""


def build_reformulation_messages(
    history: list[dict], question: str
) -> list[dict]:
    """Build messages that rewrite `question` into a standalone query.

    `history` is a list of {"role", "content"} turns, oldest first.
    """
    system = (
        "You rewrite the user's latest question into a single standalone "
        "search query that captures its full intent, using the conversation "
        "history to resolve references (pronouns, 'that', 'it', follow-ups). "
        "Return ONLY the rewritten query text. If the question is already "
        "standalone, return it unchanged."
    )
    history_text = "\n".join(
        f'{turn["role"]}: {turn["content"]}' for turn in history
    )
    user = (
        f"Conversation so far:\n{history_text or '(none)'}\n\n"
        f"Latest question: {question}\n\n"
        "Standalone search query:"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
