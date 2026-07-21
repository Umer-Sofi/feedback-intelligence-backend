"""Chatbot endpoints: ask a question, read conversation history."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.models.chat import ChatSession
from src.schemas.chat import ChatRequest, ChatResponse, ChatSessionOut
from src.services import chat_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def ask(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Ask the chatbot a question (optionally within a session)."""
    return chat_service.answer_question(
        db, payload.message, payload.session_id
    )


@router.get("/{session_id}", response_model=ChatSessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    """Return a chat session with its full message history."""
    session = db.get(ChatSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
