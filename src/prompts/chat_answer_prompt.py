"""Prompt for answering a question grounded in retrieved feedback."""


def build_answer_messages(
    question: str, retrieved: list[dict]
) -> list[dict]:
    """Build messages to answer `question` from retrieved feedback items."""
    system = (
        "You are a helpful analyst answering questions about customer "
        "feedback. Answer ONLY using the provided feedback items. If they "
        "do not contain the answer, say you don't have enough feedback to "
        "answer. Be concise and reference categories/sentiment where "
        "relevant. Never invent feedback."
    )
    context = "\n".join(
        f'[{i}] ({item.get("category")}/{item.get("sentiment")}) '
        f'"{item["text"]}"'
        for i, item in enumerate(retrieved, start=1)
    )
    user = (
        f"Feedback items:\n{context or '(none found)'}\n\n"
        f"Question: {question}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
