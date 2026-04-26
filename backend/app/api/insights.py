from datetime import datetime
from typing import Any, Dict, List, Optional
import time

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.logger import log_api_event
from app.models.transaction import Transaction
from app.services.insights.insight_engine import generate_insights_from_transactions

from fastapi import Depends
from app.core.security import get_current_firebase_user, check_user_access

router = APIRouter(prefix="/v1", tags=["insights"])


@router.get("/insights")
def get_insights(
    user_id: str,
    period: Optional[str] = Query(None, description="weekly, monthly, or custom"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user=Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    start_time = time.time()
    check_user_access(current_user, user_id)

    if period not in (None, "weekly", "monthly", "custom"):
        log_api_event(
            event_type="insights_request_failed",
            endpoint="/v1/insights",
            user_id=user_id,
            status="failed",
            extra={
                "reason": "invalid_period",
                "period": period,
            },
        )

        raise HTTPException(
            status_code=400,
            detail="period must be one of: weekly, monthly, custom"
        )

    if period == "custom":
        if not start_date or not end_date:
            log_api_event(
                event_type="insights_request_failed",
                endpoint="/v1/insights",
                user_id=user_id,
                status="failed",
                extra={
                    "reason": "missing_custom_dates",
                    "period": period,
                },
            )

            raise HTTPException(
                status_code=400,
                detail="start_date and end_date are required when period=custom"
            )

        if start_date > end_date:
            log_api_event(
                event_type="insights_request_failed",
                endpoint="/v1/insights",
                user_id=user_id,
                status="failed",
                extra={
                    "reason": "invalid_date_range",
                    "period": period,
                },
            )

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

    processing_time_ms = round((time.time() - start_time) * 1000, 2)

    log_api_event(
        event_type="insights_requested",
        endpoint="/v1/insights",
        user_id=user_id,
        status="success",
        processing_time_ms=processing_time_ms,
        extra={
            "period": period,
            "transaction_count": len(txs),
            "anomaly_count": insights.get("anomaly_count", 0),
        },
    )

    return {
        "user_id": user_id,
        **insights,
    }