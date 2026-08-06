"""GET analytics dashboard + weekly narrative summary."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.deps import require_admin
from src.database.database import get_db
from src.services import analytics, summarizer

# Every route here is admin-only: analytics are the product manager's view.
router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_admin)],
)


@router.get("/overview")
def overview(db: Session = Depends(get_db)) -> dict:
    """Return headline dashboard stats."""
    return analytics.overview(db)


@router.get("/summary")
def weekly_summary(
    start: Optional[date] = None,
    db: Session = Depends(get_db),
) -> dict:
    """Return the RAG-grounded summary for one week.

    `start` (YYYY-MM-DD) picks the week; omit it for the last 7 days.
    """
    return {"summary": summarizer.generate_weekly_summary(db, start=start)}
