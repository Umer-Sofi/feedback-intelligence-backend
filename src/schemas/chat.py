"""Pydantic schemas for the chatbot API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """A question sent by the client to the chatbot."""

    message: str = Field(min_length=1)
    session_id: Optional[int] = None


class SourceOut(BaseModel):
    """A feedback item cited as grounding for the answer."""

    feedback_id: int
    text: str


class ChatResponse(BaseModel):
    """The chatbot's grounded answer, its session, and its sources."""

    session_id: int
    answer: str
    sources: list[SourceOut] = Field(default_factory=list)


class ChatMessageOut(BaseModel):
    """A single stored chat message (one turn)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime


class ChatSessionOut(BaseModel):
    """A chat session with its full message history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: Optional[str] = None
    created_at: datetime
    messages: list[ChatMessageOut] = Field(default_factory=list)
