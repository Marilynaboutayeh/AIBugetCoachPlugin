from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.transaction import Transaction
from app.services.chatbot.intent_detector import ChatIntent, detect_intent_from_text
from app.services.chatbot.predefined_questions import (
    get_available_questions,
    get_intent_from_question_id,
)
from app.services.chatbot.response_builder import build_chat_response
from app.services.insights.insight_engine import generate_insights_from_transactions


router = APIRouter(prefix="/v1/chat", tags=["Chatbot"])


class ChatQueryRequest(BaseModel):
    user_id: str
    question_id: Optional[str] = None
    question: Optional[str] = None
    period: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


def _parse_optional_datetime(value: Optional[str], field_name: str) -> Optional[datetime]:
    """
    Converts an optional ISO date/datetime string to datetime.
    Used for custom periods.
    """

    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a valid ISO datetime format."
        )


@router.get("/questions")
def list_chat_questions():
    """
    Returns the predefined questions that the frontend can display as buttons.
    """

    return {
        "questions": get_available_questions()
    }


@router.post("/query")
def chat_query(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
):
    """
    Controlled conversational query endpoint.

    Main path:
    - Use predefined question_id.

    Fallback path:
    - If question_id is missing, try to detect intent from free-text question.

    The answer is generated only from analyzed transaction insights.
    """

    # 1. Resolve intent
    if request.question_id:
        intent = get_intent_from_question_id(request.question_id)
    else:
        intent = detect_intent_from_text(request.question)

    # 2. If unsupported, return directly without querying transactions
    if intent == ChatIntent.UNSUPPORTED:
        return {
            "question_id": request.question_id,
            "question": request.question,
            "intent": intent.value,
            **build_chat_response(intent, insights={}),
        }

    # 3. Validate custom period
    start_date = _parse_optional_datetime(request.start_date, "start_date")
    end_date = _parse_optional_datetime(request.end_date, "end_date")

    if request.period == "custom" and (start_date is None or end_date is None):
        raise HTTPException(
            status_code=400,
            detail="start_date and end_date are required when period is custom."
        )

    # 4. Fetch this user's transactions from the database
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == request.user_id)
        .all()
    )

    # 5. Generate insights using your existing insight engine
    insights = generate_insights_from_transactions(
        txs=txs,
        period=request.period,
        start_date=start_date,
        end_date=end_date,
    )

    # 6. Build chatbot response using only the generated insights
    response = build_chat_response(intent, insights)

    return {
        "question_id": request.question_id,
        "question": request.question,
        "intent": intent.value,
        **response,
    }