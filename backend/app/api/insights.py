from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.transaction import Transaction
from app.services.insights.insight_engine import generate_insights_from_transactions

router = APIRouter(prefix="/v1", tags=["insights"])


@router.get("/insights")
def get_insights(
    user_id: str,
    period: Optional[str] = Query(None, description="weekly, monthly, or custom"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    if period not in (None, "weekly", "monthly", "custom"):
        raise HTTPException(
            status_code=400,
            detail="period must be one of: weekly, monthly, custom"
        )

    if period == "custom":
        if not start_date or not end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date and end_date are required when period=custom"
            )
        if start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )

    txs: List[Transaction] = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .all()
    )

    insights = generate_insights_from_transactions(
        txs,
        period=period,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "user_id": user_id,
        **insights,
    }