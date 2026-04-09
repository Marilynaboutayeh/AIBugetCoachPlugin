from datetime import datetime
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.transaction import Transaction
from app.services.categorizer import categorize

router = APIRouter(prefix="/v1", tags=["transactions"])


class TransactionIn(BaseModel):
    merchant_description: str = Field(..., example="Carrefour Beirut")
    mcc: str = Field(..., example="5411")
    city: str = Field(..., example="Beirut")
    country: str = Field(..., example="LB")

    user_id: Optional[str] = Field(None, example="user_123")
    transaction_id: Optional[str] = Field(None, example="tx_001")
    timestamp: Optional[datetime] = None
    amount: Optional[float] = None
    currency: Optional[str] = Field(None, example="USD")
    direction: Optional[Literal["debit", "credit"]] = None


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    stored_total_for_user: int


class TransactionIn(BaseModel):
    merchant_description: str = Field(..., example="Carrefour Beirut")
    mcc: str = Field(..., example="5411")
    city: str = Field(..., example="Beirut")
    country: str = Field(..., example="LB")

    user_id: Optional[str] = Field(None, example="user_123")
    transaction_id: Optional[str] = Field(None, example="tx_001")
    timestamp: Optional[datetime] = None
    amount: Optional[float] = None
    currency: Optional[str] = Field(None, example="USD")
    direction: Optional[Literal["debit", "credit"]] = None


class IngestResponse(BaseModel):
    accepted: int
    rejected: int
    stored_total_for_user: int


class CategoryUpdateIn(BaseModel):
    predicted_main_category: str = Field(..., example="Entertainment & Leisure")
    predicted_main_category_description: Optional[str] = Field(
        None, example="Entertainment spending"
    )
    predicted_subcategory: Optional[str] = Field(
        None, example="Digital Services"
    )
    predicted_subcategory_description: Optional[str] = Field(
        None, example="Online subscriptions"
    )
    predicted_sub_subcategory: Optional[str] = Field(
        None, example="Streaming"
    )



@router.post("/transactions:ingest", response_model=IngestResponse)
def ingest_transactions(transactions: List[TransactionIn], db: Session = Depends(get_db)):
    accepted = 0
    rejected = 0

    for tx in transactions:
        if tx.user_id and tx.transaction_id:
            exists = (
                db.query(Transaction)
                .filter(
                    Transaction.user_id == tx.user_id,
                    Transaction.transaction_id == tx.transaction_id
                )
                .first()
            )
            if exists:
                rejected += 1
                continue

        cat = categorize(
            merchant_description=tx.merchant_description,
            mcc=tx.mcc,
            city=tx.city,
            country=tx.country,
        )

        db.add(
            Transaction(
                user_id=tx.user_id,
                transaction_id=tx.transaction_id,
                timestamp=tx.timestamp,
                amount=tx.amount,
                currency=tx.currency,
                direction=tx.direction,
                merchant_description=tx.merchant_description,
                mcc=tx.mcc,
                city=tx.city,
                country=tx.country,
                predicted_main_category=cat.get("main_category"),
                predicted_main_category_description=cat.get("main_category_description"),
                predicted_subcategory=cat.get("subcategory"),
                predicted_subcategory_description=cat.get("subcategory_description"),
                predicted_sub_subcategory=cat.get("sub_subcategory"),
                confidence=cat.get("confidence"),
                classification_source=cat.get("classification_source"),
                matched_by=cat.get("matched_by"),
            )
        )
        accepted += 1

    db.commit()

    stored_total_for_user = (
        db.query(Transaction)
        .filter(Transaction.user_id == transactions[0].user_id)
        .count()
        if transactions and transactions[0].user_id
        else 0
    )

    return {
        "accepted": accepted,
        "rejected": rejected,
        "stored_total_for_user": stored_total_for_user,
    }


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
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "amount": t.amount,
                "currency": t.currency,
                "direction": t.direction,
                "merchant_description": t.merchant_description,
                "mcc": t.mcc,
                "city": t.city,
                "country": t.country,
                "predicted_main_category": t.predicted_main_category,
                "predicted_main_category_description": t.predicted_main_category_description,
                "predicted_subcategory": t.predicted_subcategory,
                "predicted_subcategory_description": t.predicted_subcategory_description,
                "predicted_sub_subcategory": t.predicted_sub_subcategory,
                "confidence": t.confidence,
                "classification_source": t.classification_source,
                "matched_by": t.matched_by,
            }
            for t in txs
        ],
    }


@router.get("/transactions/{transaction_id}/category")
def get_transaction_category(transaction_id: str, user_id: str, db: Session = Depends(get_db)):
    tx = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_id == transaction_id,
        )
        .first()
    )

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "user_id": tx.user_id,
        "transaction_id": tx.transaction_id,
        "merchant_description": tx.merchant_description,
        "mcc": tx.mcc,
        "city": tx.city,
        "country": tx.country,
        "predicted_main_category": tx.predicted_main_category,
        "predicted_main_category_description": tx.predicted_main_category_description,
        "predicted_subcategory": tx.predicted_subcategory,
        "predicted_subcategory_description": tx.predicted_subcategory_description,
        "predicted_sub_subcategory": tx.predicted_sub_subcategory,
        "confidence": tx.confidence,
        "classification_source": tx.classification_source,
        "matched_by": tx.matched_by,
    }

@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str, user_id: str, db: Session = Depends(get_db)):
    tx = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_id == transaction_id,
        )
        .first()
    )

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return {
        "user_id": tx.user_id,
        "transaction_id": tx.transaction_id,
        "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
        "amount": tx.amount,
        "currency": tx.currency,
        "direction": tx.direction,
        "merchant_description": tx.merchant_description,
        "mcc": tx.mcc,
        "city": tx.city,
        "country": tx.country,
        "predicted_main_category": tx.predicted_main_category,
        "predicted_main_category_description": tx.predicted_main_category_description,
        "predicted_subcategory": tx.predicted_subcategory,
        "predicted_subcategory_description": tx.predicted_subcategory_description,
        "predicted_sub_subcategory": tx.predicted_sub_subcategory,
        "confidence": tx.confidence,
        "classification_source": tx.classification_source,
        "matched_by": tx.matched_by,
    }

@router.patch("/transactions/{transaction_id}/category")
def update_transaction_category(
    transaction_id: str,
    payload: CategoryUpdateIn,
    user_id: str,
    db: Session = Depends(get_db),
):
    tx = (
        db.query(Transaction)
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_id == transaction_id,
        )
        .first()
    )

    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tx.predicted_main_category = payload.predicted_main_category
    tx.predicted_main_category_description = payload.predicted_main_category_description
    tx.predicted_subcategory = payload.predicted_subcategory
    tx.predicted_subcategory_description = payload.predicted_subcategory_description
    tx.predicted_sub_subcategory = payload.predicted_sub_subcategory

    tx.classification_source = "manual_override"
    tx.confidence = 1.0

    db.commit()
    db.refresh(tx)

    return {
        "message": "Transaction category updated successfully",
        "user_id": tx.user_id,
        "transaction_id": tx.transaction_id,
        "predicted_main_category": tx.predicted_main_category,
        "predicted_main_category_description": tx.predicted_main_category_description,
        "predicted_subcategory": tx.predicted_subcategory,
        "predicted_subcategory_description": tx.predicted_subcategory_description,
        "predicted_sub_subcategory": tx.predicted_sub_subcategory,
        "confidence": tx.confidence,
        "classification_source": tx.classification_source,
    }