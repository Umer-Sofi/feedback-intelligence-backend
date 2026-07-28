"""RAG chatbot: reformulate -> retrieve -> answer -> persist the turn."""

from typing import Optional

from sqlalchemy.orm import Session

from src.core.config import get_settings
from src.models.chat import ChatMessage, ChatSession
from src.prompts.chat_answer_prompt import build_answer_messages
from src.prompts.query_reformulation import build_reformulation_messages
from src.schemas.chat import ChatResponse, SourceOut
from src.services import retrieval
from src.services.openai_client import chat

settings = get_settings()


def _get_or_create_session(
    db: Session, session_id: Optional[int]
) -> ChatSession:
    if session_id is not None:
        session = db.get(ChatSession, session_id)
        if session is not None:
            return session
    session = ChatSession()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def _history(session: ChatSession) -> list[dict]:
    return [
        {"role": m.role, "content": m.content} for m in session.messages
    ]


def answer_question(
    db: Session, question: str, session_id: Optional[int] = None
) -> ChatResponse:
    """Answer a question with RAG and persist the conversation turn."""
    session = _get_or_create_session(db, session_id)
    history = _history(session)

    # Give a brand-new session a readable title from its first question,
    # so the sessions list shows the topic instead of "Session 3".
    if session.title is None:
        session.title = question[:60]

    # 1. Rewrite a follow-up into a standalone retrieval query.
    if history:
        standalone = chat(
            build_reformulation_messages(history, question),
            model=settings.openai_chat_model,
        ).strip()
    else:
        standalone = question

    # 2. Retrieve relevant feedback (RAG).
    retrieved = retrieval.retrieve_relevant(db, standalone, n_results=5)

    # 3. Generate a grounded answer.
    answer = chat(
        build_answer_messages(question, retrieved),
        model=settings.openai_chat_model,
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
