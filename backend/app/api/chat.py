from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import (
    get_authenticated_anon_user_id,
    get_current_firebase_user,
    is_admin_user,
)
from app.models.transaction import Transaction
from app.services.chatbot.intent_detector import ChatIntent, detect_intent_from_text
from app.services.chatbot.predefined_questions import (
    get_available_questions,
    get_intent_from_question_id,
    get_question_text_from_id,
)
from app.services.chatbot.response_builder import build_chat_response
from app.services.insights.insight_engine import generate_insights_from_transactions
from app.services.chatbot.openai_response import generate_openai_chat_answer

router = APIRouter(prefix="/v1/chat", tags=["Chatbot"])


class ChatQueryRequest(BaseModel):
    question_id: Optional[str] = None
    question: Optional[str] = None
    period: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # Only admins can use this field.
    # Normal users must not send it.
    target_user_id: Optional[str] = None


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


def _resolve_chat_user_id(
    current_user: dict,
    target_user_id: Optional[str],
) -> str:
    """
    Resolves which anonymized user_id the chatbot should use.

    Normal user:
    - user_id is derived automatically from Firebase token email
      using config/access_control.csv.

    Admin:
    - must provide target_user_id.
    """

    if is_admin_user(current_user):
        if not target_user_id:
            raise HTTPException(
                status_code=400,
                detail="Admin users must provide target_user_id for chatbot queries."
            )

        return target_user_id

    if target_user_id:
        raise HTTPException(
            status_code=403,
            detail="Normal users cannot specify target_user_id."
        )

    return get_authenticated_anon_user_id(current_user)

def _build_openai_used_data(
    request: ChatQueryRequest,
    insights: dict,
    response: dict,
) -> dict:
    """
    Builds a compact and safe context for OpenAI.

    This gives OpenAI enough analyzed data to personalize the wording,
    without sending raw transactions or sensitive information.
    """

    anomalies = insights.get("anomalies", [])

    return {
        "period": request.period,
        "start_date": request.start_date,
        "end_date": request.end_date,

        # Deterministic chatbot result
        "base_used_data": response.get("used_data", {}),

        # Compact analyzed insight summary
        "summary": {
            "total_spent": insights.get("total_spent"),
            "spend_by_category": insights.get("spend_by_category"),
            "top_category": insights.get("top_category"),

            "current_total_spent": insights.get("current_total_spent"),
            "previous_total_spent": insights.get("previous_total_spent"),
            "change_amount": insights.get("change_amount"),
            "change_percentage": insights.get("change_percentage"),

            "anomaly_count": len(anomalies) if isinstance(anomalies, list) else 0,
        },
    }

@router.get("/questions")
def list_chat_questions(
    current_user: dict = Depends(get_current_firebase_user),
):
    """
    Returns predefined chatbot questions for authenticated users.
    """

    return {
        "questions": get_available_questions()
    }


@router.post("/query")
def chat_query(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_firebase_user),
):
    """
    Controlled conversational query endpoint.

    Main path:
    - Use predefined question_id.

    Fallback path:
    - If question_id is missing, try to detect intent from free-text question.

    Authorization:
    - Normal users do not send user_id.
    - Their anonymized user_id is derived from the authenticated Firebase user.
    - Admin users must provide target_user_id.
    """

    # 1. Resolve which anonymized user_id to use
    resolved_user_id = _resolve_chat_user_id(
        current_user=current_user,
        target_user_id=request.target_user_id,
    )

    # 2. Resolve intent
    if request.question_id:
        intent = get_intent_from_question_id(request.question_id)
    else:
        intent = detect_intent_from_text(request.question)

    # 3. If unsupported, return directly without querying transactions
    if intent == ChatIntent.UNSUPPORTED:
        return {
            "resolved_user_id": resolved_user_id,
            "question_id": request.question_id,
            "question": request.question,
            "intent": intent.value,
            **build_chat_response(intent, insights={}),
        }

    # 4. Validate custom period
    start_date = _parse_optional_datetime(request.start_date, "start_date")
    end_date = _parse_optional_datetime(request.end_date, "end_date")

    if request.period == "custom" and (start_date is None or end_date is None):
        raise HTTPException(
            status_code=400,
            detail="start_date and end_date are required when period is custom."
        )

    # 5. Fetch only the resolved anonymized user's transactions
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == resolved_user_id)
        .all()
    )

    # 6. Generate insights using your existing insight engine
    insights = generate_insights_from_transactions(
        txs=txs,
        period=request.period,
        start_date=start_date,
        end_date=end_date,
    )

    # 7. Build chatbot response using only the generated insights
    response = build_chat_response(intent, insights)

    # return {
    #     "resolved_user_id": resolved_user_id,
    #     "question_id": request.question_id,
    #     "question": request.question,
    #     "intent": intent.value,
    #     **response,
    # }

    # base_answer = response["answer"]

    # final_answer = generate_openai_chat_answer(
    #     intent=intent.value,
    #     base_answer=base_answer,
    #     used_data=response.get("used_data", {}),
    #     data_sources=response.get("data_sources", []),
    #     user_question=request.question,
    # )
    base_answer = response["answer"]

    effective_question = request.question

    if not effective_question and request.question_id:
        effective_question = get_question_text_from_id(request.question_id)

    openai_used_data = _build_openai_used_data(
        request=request,
        insights=insights,
        response=response,
    )

    final_answer = generate_openai_chat_answer(
        intent=intent.value,
        base_answer=base_answer,
        used_data=openai_used_data,
        data_sources=response.get("data_sources", []),
        # user_question=request.question,
        user_question=effective_question,
    )

    # return {
    #     "resolved_user_id": resolved_user_id,
    #     "question_id": request.question_id,
    #     "question": request.question,
    #     "intent": intent.value,
    #     "answer": final_answer,
    #     "base_answer": base_answer,
    #     "confidence": response.get("confidence"),
    #     "used_data": response.get("used_data", {}),
    #     "data_sources": response.get("data_sources", []),
    # }

    return {
        "resolved_user_id": resolved_user_id,
        "question_id": request.question_id,
        "question": request.question,
        "effective_question": effective_question,
        "intent": intent.value, 
        "answer": final_answer,
        "base_answer": base_answer,
        "confidence": response.get("confidence"),
        "used_data": response.get("used_data", {}),
        "openai_used_data": openai_used_data,
        "data_sources": response.get("data_sources", []),
    }