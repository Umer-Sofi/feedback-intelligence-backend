"""Feedback endpoints: submit new feedback and list/filter processed records."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants import Category, Sentiment
from src.database.database import get_db
from src.models.feedback import Feedback
from src.schemas.feedback import FeedbackCreate, FeedbackOut
from src.services.pipeline import process_feedback_item

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=201)
def create_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
):
    """Accept new feedback, classify + theme it now, then store it."""
    item = Feedback(
        text=payload.text,
        created_at=datetime.now(timezone.utc),
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    process_feedback_item(db, item)
    db.refresh(item)
    return item


@router.get("", response_model=list[FeedbackOut])
def list_feedback(
    db: Session = Depends(get_db),
    category: Optional[Category] = None,
    sentiment: Optional[Sentiment] = None,
    flagged: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List processed feedback, optionally filtered."""
    stmt = select(Feedback).where(Feedback.processed.is_(True))
    if category is not None:
        stmt = stmt.where(Feedback.category == category.value)
    if sentiment is not None:
        stmt = stmt.where(Feedback.sentiment == sentiment.value)
    if flagged is not None:
        stmt = stmt.where(Feedback.flagged_for_review.is_(flagged))
    stmt = (
        stmt.order_by(Feedback.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars())


@router.get("/{feedback_id}", response_model=FeedbackOut)
def get_feedback(feedback_id: int, db: Session = Depends(get_db)):
    """Get a single processed feedback record by id."""
    item = db.get(Feedback, feedback_id)
    if item is None or not item.processed:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return item
