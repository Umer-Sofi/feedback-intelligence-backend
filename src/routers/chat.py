"""Chatbot endpoints: ask a question, list/read/delete sessions."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.deps import get_current_user
from src.database.database import get_db
from src.models.chat import ChatSession
from src.models.user import User
from src.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionOut,
    ChatSessionSummary,
)
from src.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def ask(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Ask the chatbot a question (scoped to the caller; admins see all)."""
    return chat_service.answer_question(
        db, payload.message, payload.session_id, current_user
    )


@router.get("/sessions", response_model=list[ChatSessionSummary])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List the caller's own chat sessions, newest first."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
    )
    return list(db.execute(stmt).scalars())


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return one of the caller's sessions with its full history."""
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete one of the caller's sessions and its messages (cascade)."""
    session = db.get(ChatSession, session_id)
    if session is None or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)  # cascade removes the session's chat_messages too
    db.commit()
