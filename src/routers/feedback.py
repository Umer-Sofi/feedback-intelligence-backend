"""Feedback endpoints: submit new feedback and list/filter processed records."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.constants import Category, Sentiment
from src.core.deps import get_current_user, require_admin
from src.database.database import get_db
from src.models.feedback import Feedback
from src.models.user import User
from src.schemas.feedback import (
    FeedbackCreate,
    FeedbackOut,
    FeedbackUpdate,
)
from src.services.pipeline import process_feedback_item

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackOut, status_code=201)
def create_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept new feedback, stamp the owner, classify + theme it, store."""
    item = Feedback(
        text=payload.text,
        created_at=datetime.now(timezone.utc),
        user_id=current_user.id,
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
    current_user: User = Depends(get_current_user),
    category: Optional[Category] = None,
    sentiment: Optional[Sentiment] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List processed feedback.

    Admins see everything; a regular user sees only their own feedback
    (this doubles as their "My history" view).
    """
    stmt = select(Feedback).where(Feedback.processed.is_(True))
    if current_user.role != "admin":
        stmt = stmt.where(Feedback.user_id == current_user.id)
    if category is not None:
        # category may be a comma-separated list; match if it contains the
        # requested value (no category value is a substring of another).
        stmt = stmt.where(Feedback.category.contains(category.value))
    if sentiment is not None:
        stmt = stmt.where(Feedback.sentiment == sentiment.value)
    if status is not None:
        stmt = stmt.where(Feedback.status == status)
    stmt = (
        stmt.order_by(Feedback.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(stmt).scalars())


@router.get("/{feedback_id}", response_model=FeedbackOut)
def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single processed feedback record (own, or any if admin)."""
    item = db.get(Feedback, feedback_id)
    if item is None or not item.processed:
        raise HTTPException(status_code=404, detail="Feedback not found")
    if current_user.role != "admin" and item.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return item


@router.patch("/{feedback_id}", response_model=FeedbackOut)
def update_feedback(
    feedback_id: int,
    payload: FeedbackUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Admin only: update a feedback's status and/or add a reply."""
    item = db.get(Feedback, feedback_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Feedback not found")
    if payload.status is not None:
        item.status = payload.status.value
    if payload.admin_reply is not None:
        item.admin_reply = payload.admin_reply
    db.commit()
    db.refresh(item)
    return item
