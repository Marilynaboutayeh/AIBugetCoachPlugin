from datetime import datetime
from pathlib import Path
from typing import Optional
import re

import joblib
import pandas as pd
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
from app.services.chatbot.openai_response import generate_openai_chat_answer
from app.services.chatbot.predefined_questions import (
    get_available_questions,
    get_intent_from_question_id,
    get_question_text_from_id,
)
from app.services.chatbot.response_builder import build_chat_response
from app.services.forecast.feature_builder import build_forecast_features
from app.services.forecast.recurring_detector import detect_recurring_candidates
from app.services.insights.insight_engine import generate_insights_from_transactions


router = APIRouter(prefix="/v1/chat", tags=["Chatbot"])


# Path:
# backend/app/api/chat.py
# backend/app/services/forecast/subscription_model.pkl
FORECAST_MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "services"
    / "forecast"
    / "subscription_model.pkl"
)

try:
    subscription_model = joblib.load(FORECAST_MODEL_PATH)
    print("Subscription forecast model loaded successfully.")
except Exception as e:
    print("Subscription forecast model failed to load:", repr(e))
    subscription_model = None


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
            detail=f"{field_name} must be a valid ISO datetime format.",
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
                detail="Admin users must provide target_user_id for chatbot queries.",
            )

        return target_user_id

    if target_user_id:
        raise HTTPException(
            status_code=403,
            detail="Normal users cannot specify target_user_id.",
        )

    return get_authenticated_anon_user_id(current_user)


def _reject_cross_user_question(
    question: Optional[str],
    resolved_user_id: str,
    current_user: dict,
) -> None:
    """
    Rejects normal users if their free-text question tries to access
    another anonymized user_id such as user_2 or anon_123.

    Admin users are allowed because their access is controlled through target_user_id.
    """

    if not question:
        return

    if is_admin_user(current_user):
        return

    mentioned_user_ids = re.findall(
        r"\b(user_\d+|anon_\d+)\b",
        question.lower(),
    )

    for mentioned_user_id in mentioned_user_ids:
        if mentioned_user_id != resolved_user_id.lower():
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to access another user's data.",
            )


def _add_recurring_context(
    chat_context: dict,
    txs,
) -> None:
    """
    Adds recurring expense / subscription candidates using Sophia's forecast pipeline:

    - recurring_detector.py
    - feature_builder.py
    - subscription_model.pkl

    It does not return raw Transaction objects to the chatbot/OpenAI.
    """

    try:
        candidates = detect_recurring_candidates(txs)
        public_candidates = []

        for candidate in candidates:
            candidate_transactions = candidate.get("transactions", [])

            features = build_forecast_features(candidate_transactions)

            if not features:
                continue

            ml_prediction_is_recurring = None
            ml_confidence = None

            if subscription_model is not None:
                features_df = pd.DataFrame([features])

                prediction = subscription_model.predict(features_df)[0]
                ml_prediction_is_recurring = int(prediction)

                if hasattr(subscription_model, "predict_proba"):
                    probability = subscription_model.predict_proba(features_df)[0]
                    ml_confidence = round(float(probability[1]), 4)

            public_candidates.append(
                {
                    "merchant": candidate.get("merchant"),
                    "frequency": candidate.get("frequency"),
                    "matched_transactions": candidate.get("matched_transactions"),
                    "occurrence_count": candidate.get("matched_transactions"),
                    "average_amount": candidate.get("average_amount"),
                    "avg_amount": candidate.get("average_amount"),
                    "last_transaction_date": candidate.get("last_transaction_date"),

                    # ML forecast result
                    "ml_prediction_is_recurring": ml_prediction_is_recurring,
                    "ml_confidence": ml_confidence,
                    "confidence": ml_confidence,

                    # Safe feature summary, no raw transactions
                    "features": features,
                }
            )

        chat_context["recurring_candidates"] = public_candidates

    except Exception as e:
        print("Recurring forecast context failed:", repr(e))
        chat_context["recurring_candidates"] = []


def _add_cashflow_forecast_context(chat_context: dict) -> None:
    """
    Builds a simple cashflow forecast context from recurring candidates.

    This does not create a new forecasting model.
    It estimates expected upcoming recurring outflow from detected recurring payments.
    """

    recurring_candidates = chat_context.get("recurring_candidates", [])

    confirmed_or_rule_based_candidates = []

    for item in recurring_candidates:
        prediction = item.get("ml_prediction_is_recurring")

        # If model predicts recurring, include it.
        # If model is unavailable and prediction is None, keep the rule-based candidate.
        if prediction == 1 or prediction is True or prediction is None:
            confirmed_or_rule_based_candidates.append(item)

    if not confirmed_or_rule_based_candidates:
        chat_context["cashflow_forecast"] = None
        return

    expected_total = 0.0

    for item in confirmed_or_rule_based_candidates:
        amount = item.get("average_amount") or item.get("avg_amount") or 0

        try:
            expected_total += float(amount)
        except (TypeError, ValueError):
            continue

    expected_total = round(expected_total, 2)

    chat_context["cashflow_forecast"] = {
        "forecast_type": "recurring_expense_based_forecast",
        "forecast_period": "next period",
        "expected_total": expected_total,
        "recurring_items_count": len(confirmed_or_rule_based_candidates),
        "recurring_candidates": confirmed_or_rule_based_candidates,
        "message": (
            f"Based on detected recurring payments, the expected recurring outflow "
            f"for the next period is {expected_total}."
        ),
    }


def _build_chat_context(
    txs,
    resolved_user_id: str,
    db: Session,
    request: ChatQueryRequest,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
) -> dict:
    """
    Builds one combined chatbot context using all available backend services.

    Sources:
    - Insight engine
    - Anomaly logic inside insights
    - Merchant/category insights inside insights
    - Sophia's recurring forecast pipeline
    - Simple cashflow forecast based on recurring candidates
    """

    insights = generate_insights_from_transactions(
        txs=txs,
        period=request.period,
        start_date=start_date,
        end_date=end_date,
    )

    chat_context = {
        "insights": insights,
        "resolved_user_id": resolved_user_id,
    }

    # Keep response_builder compatibility.
    # This lets response_builder read keys directly like total_spent, anomalies, etc.
    if isinstance(insights, dict):
        chat_context.update(insights)

    _add_recurring_context(
        chat_context=chat_context,
        txs=txs,
    )

    _add_cashflow_forecast_context(
        chat_context=chat_context,
    )

    return chat_context


def _build_openai_used_data(
    request: ChatQueryRequest,
    chat_context: dict,
    response: dict,
) -> dict:
    """
    Builds a compact and safe context for OpenAI.

    This gives OpenAI analyzed backend data only.
    It does not send raw transactions.
    """

    anomalies = chat_context.get("anomalies", [])

    return {
        "period": request.period,
        "start_date": request.start_date,
        "end_date": request.end_date,

        # Deterministic chatbot result
        "base_used_data": response.get("used_data", {}),

        # Compact analyzed context from all services
        "summary": {
            "total_spent": chat_context.get("total_spent"),
            "spend_by_category": chat_context.get("spend_by_category"),
            "top_category": chat_context.get("top_category"),

            "current_total_spent": chat_context.get("current_total_spent"),
            "previous_total_spent": chat_context.get("previous_total_spent"),
            "change_amount": chat_context.get("change_amount"),
            "change_percentage": chat_context.get("change_percentage"),

            "top_merchants_by_spend": (
                chat_context.get("top_merchants_by_spend")
                or chat_context.get("top_merchants")
            ),
            "repeated_merchants": chat_context.get("repeated_merchants"),
            "concentrated_spending": chat_context.get("concentrated_spending"),

            "anomaly_count": len(anomalies) if isinstance(anomalies, list) else 0,
            "anomalies": anomalies[:3] if isinstance(anomalies, list) else [],

            "recurring_candidates": chat_context.get("recurring_candidates"),
            "cashflow_forecast": chat_context.get("cashflow_forecast"),
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

    Data flow:
    - Resolve user
    - Reject cross-user questions for normal users
    - Detect intent
    - Build chatbot context from insights and forecast components
    - Build deterministic base answer
    - Optionally rewrite with OpenAI
    """

    # 1. Resolve which anonymized user_id to use
    resolved_user_id = _resolve_chat_user_id(
        current_user=current_user,
        target_user_id=request.target_user_id,
    )

    # 1.1 Reject normal users trying to ask about another anonymized user
    _reject_cross_user_question(
        question=request.question,
        resolved_user_id=resolved_user_id,
        current_user=current_user,
    )

    # 2. Resolve intent
    if request.question_id:
        intent = get_intent_from_question_id(request.question_id)
    else:
        intent = detect_intent_from_text(request.question)

    # 3. If unsupported, return directly without querying transactions
    if intent == ChatIntent.UNSUPPORTED:
        unsupported_response = build_chat_response(intent, insights={})

        return {
            "resolved_user_id": resolved_user_id,
            "question_id": request.question_id,
            "question": request.question,
            "effective_question": request.question,
            "intent": intent.value,
            "answer": unsupported_response.get("answer"),
            "base_answer": unsupported_response.get("answer"),
            "confidence": unsupported_response.get("confidence"),
            "used_data": unsupported_response.get("used_data", {}),
            "openai_used_data": {},
            "data_sources": unsupported_response.get("data_sources", []),
        }

    # 4. Validate custom period
    start_date = _parse_optional_datetime(request.start_date, "start_date")
    end_date = _parse_optional_datetime(request.end_date, "end_date")

    if request.period == "custom" and (start_date is None or end_date is None):
        raise HTTPException(
            status_code=400,
            detail="start_date and end_date are required when period is custom.",
        )

    # 5. Fetch only the resolved anonymized user's transactions
    txs = (
        db.query(Transaction)
        .filter(Transaction.user_id == resolved_user_id)
        .all()
    )

    # 6. Build combined chatbot context from insights and forecast components
    chat_context = _build_chat_context(
        txs=txs,
        resolved_user_id=resolved_user_id,
        db=db,
        request=request,
        start_date=start_date,
        end_date=end_date,
    )

    # 7. Build deterministic chatbot response from backend context
    response = build_chat_response(intent, chat_context)

    base_answer = response["answer"]

    # 8. Resolve effective question for OpenAI
    effective_question = request.question

    if not effective_question and request.question_id:
        effective_question = get_question_text_from_id(request.question_id)

    # 9. Build OpenAI-safe context
    openai_used_data = _build_openai_used_data(
        request=request,
        chat_context=chat_context,
        response=response,
    )

    # 10. OpenAI only rewrites the backend-generated answer.
    # If OpenAI is missing/failing, generate_openai_chat_answer returns base_answer.
    final_answer = generate_openai_chat_answer(
        intent=intent.value,
        base_answer=base_answer,
        used_data=openai_used_data,
        data_sources=response.get("data_sources", []),
        user_question=effective_question,
    )

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