from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.transaction import Transaction
from app.services.insights.insight_engine import generate_insights_from_transactions

router = APIRouter(prefix="/v1", tags=["insights"])


@router.get("/insights")
def get_insights(user_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    txs: List[Transaction] = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .all()
    )

    insights = generate_insights_from_transactions(txs)

    return {
        "user_id": user_id,
        **insights,
    }