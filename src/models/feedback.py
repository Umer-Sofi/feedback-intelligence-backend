"""ORM models for feedback, its embedded chunks, and their themes."""

from datetime import datetime
from typing import Optional

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.config import get_settings
from src.database.database import Base

_EMBEDDING_DIM = get_settings().embedding_dim


class Theme(Base):
    """A recurring topic that similar feedback items are grouped under."""

    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(200))
    keywords: Mapped[Optional[str]] = mapped_column(Text, default=None)

    # Vector of the theme's keywords — powers nearest-theme matching.
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(_EMBEDDING_DIM), default=None
    )

    feedback_items: Mapped[list["Feedback"]] = relationship(
        back_populates="theme"
    )


class Feedback(Base):
    """A single piece of customer feedback plus its classification."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # Classification output — null until the pipeline processes the row.
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    # May hold several categories, comma-separated, for multi-topic feedback.
    category: Mapped[Optional[str]] = mapped_column(String(200), default=None)
    sentiment: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Float, default=None
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, default=None)

    # Owner — the user who submitted it (null for legacy dataset rows).
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), default=None
    )

    # Workflow: lifecycle status, an optional admin reply, and an
    # AI-derived priority (High/Medium/Low). See steps 4-5.
    status: Mapped[str] = mapped_column(String(20), default="open")
    admin_reply: Mapped[Optional[str]] = mapped_column(Text, default=None)
    priority: Mapped[Optional[str]] = mapped_column(String(10), default=None)

    # Theme link — assigned by the theme aggregator via vector similarity.
    theme_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("themes.id"), default=None
    )
    theme: Mapped[Optional["Theme"]] = relationship(
        back_populates="feedback_items"
    )

    # Embedded text passages — one-to-many so a long feedback can be split
    # into several separately-embedded chunks. Powers RAG retrieval.
    chunks: Mapped[list["FeedbackChunk"]] = relationship(
        back_populates="feedback",
        cascade="all, delete-orphan",
    )


class FeedbackChunk(Base):
    """One embedded passage of a feedback item (a feedback has one or more)."""

    __tablename__ = "feedback_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)
    feedback_id: Mapped[int] = mapped_column(
        ForeignKey("feedback.id"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk_text: Mapped[str] = mapped_column(Text)

    # Vector of this chunk's text — powers RAG retrieval.
    embedding: Mapped[Optional[list[float]]] = mapped_column(
        Vector(_EMBEDDING_DIM), default=None
    )

    feedback: Mapped["Feedback"] = relationship(back_populates="chunks")
