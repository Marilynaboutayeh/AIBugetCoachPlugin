from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.transaction import Transaction
from app.services.categorizer import categorize

router = APIRouter(prefix="/v1", tags=["transactions"])


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


@router.post("/transactions:ingest", response_model=IngestResponse)
def ingest_transactions(transactions: List[TransactionIn], db: Session = Depends(get_db)):
    accepted = 0
    rejected = 0

    for tx in transactions:
        exists = (
            db.query(Transaction)
            .filter(Transaction.user_id == tx.user_id, Transaction.transaction_id == tx.transaction_id)
            .first()
        )
        if exists:
            rejected += 1
            continue

        cat = categorize(tx.merchant, tx.description)

        db.add(
            Transaction(
                user_id=tx.user_id,
                transaction_id=tx.transaction_id,
                timestamp=tx.timestamp,
                amount=tx.amount,
                currency=tx.currency,
                direction=tx.direction,
                merchant=tx.merchant,
                description=tx.description,
                category=cat,
            )
        )
        accepted += 1

    db.commit()

    stored_total_for_user = (
        db.query(Transaction).filter(Transaction.user_id == transactions[0].user_id).count()
        if transactions else 0
    )

    return {"accepted": accepted, "rejected": rejected, "stored_total_for_user": stored_total_for_user}


@router.get("/transactions")
def list_transactions(user_id: str, db: Session = Depends(get_db)):
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.timestamp.asc())
        .all()
    )

    return {
        "user_id": user_id,
        "transactions": [
            {
                "user_id": t.user_id,
                "transaction_id": t.transaction_id,
                "timestamp": t.timestamp.isoformat(),
                "amount": t.amount,
                "currency": t.currency,
                "direction": t.direction,
                "merchant": t.merchant,
                "description": t.description,
                "category": t.category,
            }
            for t in txs
        ],
    }