"""Prompt for answering a question grounded in retrieved feedback."""


def build_answer_messages(
    question: str,
    retrieved: list[dict],
    personal: bool = False,
    listing: bool = False,
) -> list[dict]:
    """Build messages to answer `question` from retrieved feedback items.

    `personal` marks the user-scoped bot: the provided items are the current
    user's OWN feedback, so the assistant should treat and refer to them as
    "your feedback" rather than generic customer feedback.

    `listing` marks a "recent/list" request: the items are ordered
    most-recent-first, so the assistant should present them as a list.
    """
    if personal:
        system = (
            "You are a helpful assistant that helps a user explore THEIR "
            "OWN feedback. Every feedback item provided below was submitted "
            "by this same user, so treat them as the user's own feedback and "
            "refer to them as \"your feedback\". Answer using ONLY the "
            "provided items and never invent feedback. When asked to show or "
            "list their feedback, present the items clearly (noting "
            "category/sentiment where useful). If they greet you or ask about "
            "something not present in their feedback, warmly say what you can "
            "help with (their reported issues, requests, sentiment) — do not "
            "present a lack of data as a failure, and do NOT claim you lack "
            "access to their feedback."
        )
    else:
        system = (
            "You are a helpful assistant for exploring customer feedback. "
            "Answer questions using ONLY the provided feedback items, and "
            "never invent feedback. If the user greets you or asks something "
            "the feedback doesn't cover, briefly and warmly explain that you "
            "can answer questions about the customer feedback (e.g. common "
            "complaints, feature requests, pricing, sentiment) — do not "
            "present a lack of data as a failure. Be concise and reference "
            "categories/sentiment where relevant."
        )
    # Never let the model cite the retrieval position ("item 3") — the user
    # never sees those numbers, so it reads as broken. Quote/paraphrase.
    system += (
        " When you reference a specific piece of feedback, quote or "
        "paraphrase it — never refer to it by an item or index number."
    )
    if listing:
        system += (
            " The feedback items below are listed from MOST RECENT to "
            "oldest. Present them as a numbered list in that same order "
            "(most recent first), each with a short summary and its "
            "category/sentiment."
        )
    context = "\n".join(
        f'- ({item.get("category")}/{item.get("sentiment")}) "{item["text"]}"'
        for item in retrieved
    )
    user = (
        f"Feedback items:\n{context or '(none found)'}\n\n"
        f"Question: {question}"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
