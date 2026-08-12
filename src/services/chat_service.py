"""RAG chatbot: reformulate -> retrieve -> answer -> persist the turn.

Conversation memory is a sliding window: only the last few messages of the
session are replayed as context, so follow-ups resolve while the context
stays bounded no matter how long the chat grows.
"""

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.models.chat import ChatMessage, ChatSession
from src.models.feedback import Feedback
from src.models.user import User
from src.prompts.chat_answer_prompt import build_answer_messages
from src.prompts.query_reformulation import build_reformulation_messages
from src.schemas.chat import ChatResponse, SourceOut
from src.services import retrieval
from src.services.openai_client import chat

settings = get_settings()

# Conversation memory: replay only the last few messages (a question and its
# answer are two messages), so the context stays bounded as the chat grows.
_HISTORY_MESSAGES = 8

# Generous cap on the answer length (a hard stop). Plenty for a grounded
# reply; guards cost/UX against a runaway response.
_ANSWER_MAX_TOKENS = 500

# "Browse the recent feedback" requests are about time, not meaning, so they
# are routed to a newest-first DB lookup instead of vector search.
_LISTING_KEYWORDS = (
    "recent", "latest", "newest", "most recent", "list", "show me",
)
_RECENT_FEEDBACK_COUNT = 5


def _get_or_create_session(
    db: Session, session_id: Optional[int], user_id: int
) -> ChatSession:
    """Resume the user's own session if given, else start a new one.

    A session_id that belongs to someone else is ignored (a fresh session
    is created) so one user can never append to another's conversation.
    """
    if session_id is not None:
        session = db.get(ChatSession, session_id)
        if session is not None and session.user_id == user_id:
            return session
    session = ChatSession(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _recent_history(db: Session, session: ChatSession) -> list[dict]:
    """Return the last few messages of the session, oldest -> newest."""
    rows = db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
        .order_by(ChatMessage.id.desc())
        .limit(_HISTORY_MESSAGES)
    ).scalars().all()
    return [
        {"role": m.role, "content": m.content}
        for m in reversed(rows)
    ]


def _is_listing_query(question: str) -> bool:
    """True if the user is asking to browse recent feedback (not a topic)."""
    q = question.lower()
    return any(keyword in q for keyword in _LISTING_KEYWORDS)


def _recent_feedback(
    db: Session, n: int, user_id: Optional[int] = None
) -> list[dict]:
    """The n most recent processed feedback items, newest first.

    Scoped to one user when `user_id` is given (customer bot); all feedback
    when None (admin bot).
    """
    stmt = select(Feedback).where(Feedback.processed.is_(True))
    if user_id is not None:
        stmt = stmt.where(Feedback.user_id == user_id)
    rows = db.execute(
        stmt.order_by(Feedback.created_at.desc()).limit(n)
    ).scalars().all()
    return [
        {
            "feedback_id": f.id,
            "text": f.text,
            "category": f.category,
            "sentiment": f.sentiment,
        }
        for f in rows
    ]


def answer_question(
    db: Session,
    question: str,
    session_id: Optional[int],
    user: User,
) -> ChatResponse:
    """Answer a question with RAG and persist the conversation turn.

    An admin's bot searches all feedback; a customer's bot is scoped to
    their own feedback via `scope_user_id`.
    """
    scope_user_id = None if user.role == "admin" else user.id
    session = _get_or_create_session(db, session_id, user.id)

    # Give a brand-new session a readable title from its first question,
    # so the sessions list shows the topic instead of "Session 3".
    if session.title is None:
        session.title = question[:60]

    history = _recent_history(db, session)

    listing = _is_listing_query(question)
    if listing:
        # "recent/latest/list" is about time, not meaning: return the newest
        # feedback directly (vector search can't order by recency).
        retrieved = _recent_feedback(
            db, _RECENT_FEEDBACK_COUNT, scope_user_id
        )
    else:
        # 1. Rewrite a follow-up into a standalone retrieval query.
        if history:
            standalone = chat(
                build_reformulation_messages(history, question),
                model=settings.openai_chat_model,
            ).strip()
        else:
            standalone = question

        # 2. Retrieve relevant feedback (RAG), scoped to the user if needed.
        retrieved = retrieval.retrieve_relevant(
            db, standalone, n_results=5, user_id=scope_user_id
        )

    # 3. Generate a grounded answer. The user-scoped bot answers about the
    #    user's OWN feedback, so frame the items as "your feedback".
    answer = chat(
        build_answer_messages(
            question,
            retrieved,
            personal=scope_user_id is not None,
            listing=listing,
        ),
        model=settings.openai_chat_model,
        max_tokens=_ANSWER_MAX_TOKENS,
    )

    # 4. Persist both turns.
    db.add(ChatMessage(session_id=session.id, role="user", content=question))
    db.add(ChatMessage(
        session_id=session.id, role="assistant", content=answer
    ))
    db.commit()

    sources = [
        SourceOut(feedback_id=item["feedback_id"], text=item["text"])
        for item in retrieved
    ]
    return ChatResponse(session_id=session.id, answer=answer, sources=sources)
