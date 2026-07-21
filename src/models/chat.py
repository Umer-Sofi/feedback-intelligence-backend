"""ORM models for chatbot sessions and their messages."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base


def _utcnow() -> datetime:
    """Timezone-aware UTC now, used as a column default."""
    return datetime.now(timezone.utc)


class ChatSession(Base):
    """A single conversation thread with the feedback chatbot."""

    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        order_by="ChatMessage.created_at",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    """One turn (user question or assistant answer) in a session."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("chat_sessions.id"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    session: Mapped["ChatSession"] = relationship(back_populates="messages")
