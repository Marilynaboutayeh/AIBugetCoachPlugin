from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

from app.services.categorizer import categorize

router = APIRouter(prefix="/v1", tags=["transactions"])


# Schemas 
class TransactionIn(BaseModel):
    user_id: str = Field(..., example="user_123") 
    transaction_id: str = Field(..., example="tx_001")
    timestamp: datetime
    amount: float
    currency: str = Field(..., example="USD")
    direction: Literal["debit", "credit"]
    merchant: Optional[str] = None
    description: Optional[str] = None


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    stored_total_for_user: int


# Temporary in-memory storage 
FAKE_DB: dict[str, list[dict]] = {}


@router.post("/transactions:ingest", response_model=IngestResponse)
def ingest_transactions(transactions: List[TransactionIn]):
    accepted = 0
    rejected = 0

    for tx in transactions:
        user_store = FAKE_DB.setdefault(tx.user_id, [])

        # simple duplicate check: same transaction_id for same user
        if any(existing["transaction_id"] == tx.transaction_id for existing in user_store):
            rejected += 1
            continue

        data = tx.model_dump()
        data["category"] = categorize(tx.merchant, tx.description)  # to categorize the transaction sent
        user_store.append(data)
        accepted += 1

    stored_total_for_user = len(FAKE_DB.get(transactions[0].user_id, [])) if transactions else 0

    return {
        "accepted": accepted,
        "rejected": rejected,
        "stored_total_for_user": stored_total_for_user,
    }


@router.get("/transactions")
def list_transactions(user_id: str):
    """
    View what we stored for a user (for debugging/demo).
    """
    return {"user_id": user_id, "transactions": FAKE_DB.get(user_id, [])}