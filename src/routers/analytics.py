"""GET analytics dashboard + weekly narrative summary."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database.database import get_db
from src.services import analytics, summarizer

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> dict:
    """Return headline dashboard stats."""
    return analytics.overview(db)


@router.get("/summary")
def weekly_summary(db: Session = Depends(get_db)) -> dict:
    """Return the RAG-grounded weekly narrative summary."""
    return {"summary": summarizer.generate_weekly_summary(db)}
