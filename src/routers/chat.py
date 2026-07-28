"""Chatbot endpoints: ask a question, list/read/delete sessions."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.models.chat import ChatSession
from src.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionOut,
    ChatSessionSummary,
)
from src.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def ask(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Ask the chatbot a question (optionally within a session)."""
    return chat_service.answer_question(
        db, payload.message, payload.session_id
    )


@router.get("/sessions", response_model=list[ChatSessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    """List all chat sessions, newest first (for the resume picker)."""
    stmt = select(ChatSession).order_by(ChatSession.created_at.desc())
    return list(db.execute(stmt).scalars())


@router.get("/sessions/{session_id}", response_model=ChatSessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Return a chat session with its full message history."""
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a session and all its messages (cascade)."""
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)  # cascade removes the session's chat_messages too
    db.commit()
