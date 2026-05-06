from datetime import datetime
from typing import Any, Dict, List, Optional
import time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.logger import log_api_event
from app.core.security import (
    get_authenticated_anon_user_id,
    get_current_firebase_user,
    is_admin_user,
)
from app.models.transaction import Transaction
from app.services.insights.insight_engine import generate_insights_from_transactions


router = APIRouter(prefix="/v1", tags=["insights"])


def _resolve_insights_user_id(
    current_user: dict,
    target_user_id: Optional[str],
) -> Optional[str]:
    """
    Resolves which anonymized user_id should be used for insights.

    Normal user:
    - Cannot send target_user_id.
    - user_id is derived from Firebase token email using access_control.csv.

    Admin:
    - If target_user_id is provided, return that user's insights.
    - If target_user_id is missing, return all users' aggregated insights.
    """

    if is_admin_user(current_user):
        return target_user_id

    if target_user_id:
        raise HTTPException(
            status_code=403,
            detail="Normal users cannot specify target_user_id."
        )

    return get_authenticated_anon_user_id(current_user)


@router.get("/insights")
def get_insights(
    period: Optional[str] = Query(None, description="weekly, monthly, or custom"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    target_user_id: Optional[str] = Query(
        None,
        description="Admin only: anonymized user_id to inspect, for example user_1"
    ),
    current_user: dict = Depends(get_current_firebase_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    start_time = time.time()

    resolved_user_id = _resolve_insights_user_id(
        current_user=current_user,
        target_user_id=target_user_id,
    )

    log_user_id = resolved_user_id if resolved_user_id else "all"

    if period not in (None, "weekly", "monthly", "custom"):
        log_api_event(
            event_type="insights_request_failed",
            endpoint="/v1/insights",
            user_id=log_user_id,
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
                user_id=log_user_id,
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
                user_id=log_user_id,
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

    query = db.query(Transaction)

    if resolved_user_id:
        query = query.filter(Transaction.user_id == resolved_user_id)

    txs: List[Transaction] = query.all()

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
        user_id=log_user_id,
        status="success",
        processing_time_ms=processing_time_ms,
        extra={
            "period": period,
            "transaction_count": len(txs),
            "anomaly_count": insights.get("anomaly_count", 0),
        },
    )

    return {
        "resolved_user_id": log_user_id,
        **insights,
    }