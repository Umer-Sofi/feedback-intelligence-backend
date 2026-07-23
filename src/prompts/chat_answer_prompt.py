"""Prompt for answering a question grounded in retrieved feedback."""


def build_answer_messages(
    question: str, retrieved: list[dict]
) -> list[dict]:
    """Build messages to answer `question` from retrieved feedback items."""
    system = (
        "You are a helpful assistant for exploring customer feedback. "
        "Answer questions using ONLY the provided feedback items, and never "
        "invent feedback. If the user greets you or asks something the "
        "feedback doesn't cover, briefly and warmly explain that you can "
        "answer questions about the customer feedback (e.g. common "
        "complaints, feature requests, pricing, sentiment) — do not present "
        "a lack of data as a failure. Be concise and reference "
        "categories/sentiment where relevant."
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
