from fastapi import APIRouter
from typing import Dict, Any, List, Tuple

# IMPORTANT: we reuse the same in-memory storage from transactions.py
from app.api.transactions import FAKE_DB

router = APIRouter(prefix="/v1", tags=["insights"])


@router.get("/insights")
def get_insights(user_id: str) -> Dict[str, Any]:
    txs: List[dict] = FAKE_DB.get(user_id, [])

    total_spent = 0.0   # debit
    total_income = 0.0  # credit

    by_category: Dict[str, float] = {}
    by_merchant: Dict[str, float] = {}
    count = len(txs)

    for tx in txs:
        amount = float(tx["amount"])
        direction = tx["direction"]
        category = tx.get("category", "Other")
        merchant = tx.get("merchant") or "Unknown"

        if direction == "debit":
            total_spent += amount
            by_category[category] = by_category.get(category, 0.0) + amount
            by_merchant[merchant] = by_merchant.get(merchant, 0.0) + amount
        else:
            total_income += amount

    # sort helpers (top merchants)
    top_merchants: List[Tuple[str, float]] = sorted(
        by_merchant.items(), key=lambda x: x[1], reverse=True
    )[:5]

    return {
        "user_id": user_id,
        "transaction_count": count,
        "total_spent": round(total_spent, 2),
        "total_income": round(total_income, 2),
        "spend_by_category": {k: round(v, 2) for k, v in by_category.items()},
        "top_merchants_by_spend": [{"merchant": m, "amount": round(a, 2)} for m, a in top_merchants],
    }