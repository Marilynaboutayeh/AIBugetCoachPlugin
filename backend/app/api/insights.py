from fastapi import APIRouter, Depends
from typing import Dict, Any, List, Tuple

from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.transaction import Transaction

router = APIRouter(prefix="/v1", tags=["insights"])


@router.get("/insights")
def get_insights(user_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    txs: List[Transaction] = db.query(Transaction).filter(Transaction.user_id == user_id).all()

    total_spent = 0.0
    total_income = 0.0
    by_category: Dict[str, float] = {}
    by_merchant: Dict[str, float] = {}

    for tx in txs:
        amount = float(tx.amount)
        if tx.direction == "debit":
            total_spent += amount
            by_category[tx.category] = by_category.get(tx.category, 0.0) + amount
            merchant = tx.merchant or "Unknown"
            by_merchant[merchant] = by_merchant.get(merchant, 0.0) + amount
        else:
            total_income += amount

    top_merchants: List[Tuple[str, float]] = sorted(by_merchant.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "user_id": user_id,
        "transaction_count": len(txs),
        "total_spent": round(total_spent, 2),
        "total_income": round(total_income, 2),
        "spend_by_category": {k: round(v, 2) for k, v in by_category.items()},
        "top_merchants_by_spend": [{"merchant": m, "amount": round(a, 2)} for m, a in top_merchants],
    }