"""ORM models for feedback records and the themes they're grouped into."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base


def _utcnow() -> datetime:
    """Timezone-aware UTC now, used as a column default."""
    return datetime.now(timezone.utc)


class Theme(Base):
    """A recurring topic that similar feedback items are grouped under."""

    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(primary_key=True)
    label: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    feedback_items: Mapped[list["Feedback"]] = relationship(
        back_populates="theme"
    )


class Feedback(Base):
    """A single piece of customer feedback plus its classification."""

    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow
    )

    # Classification output — null until the pipeline processes the row.
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    sentiment: Mapped[Optional[str]] = mapped_column(String(20), default=None)
    sentiment_score: Mapped[Optional[float]] = mapped_column(
        Float, default=None
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, default=None)
    flagged_for_review: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=None
    )

    # Theme link — assigned by the theme aggregator via vector similarity.
    theme_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("themes.id"), default=None
    )
    theme: Mapped[Optional["Theme"]] = relationship(
        back_populates="feedback_items"
    )
