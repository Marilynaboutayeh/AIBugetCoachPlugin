from typing import Dict, List, Optional

from app.services.chatbot.intent_detector import ChatIntent


PREDEFINED_QUESTIONS: Dict[str, Dict[str, str]] = {
    # Core spending insights
    "spending_summary": {
        "question": "How much did I spend this period?",
        "intent": ChatIntent.SPENDING_SUMMARY.value,
    },
    "category_breakdown": {
        "question": "Show my spending by category.",
        "intent": ChatIntent.CATEGORY_BREAKDOWN.value,
    },
    "top_category": {
        "question": "What is my top spending category?",
        "intent": ChatIntent.TOP_CATEGORY.value,
    },
    "spending_comparison": {
        "question": "Compare my spending with the previous period.",
        "intent": ChatIntent.SPENDING_COMPARISON.value,
    },

    # Merchant insights
    "top_merchants": {
        "question": "Where did I spend the most?",
        "intent": ChatIntent.TOP_MERCHANTS.value,
    },
    "repeated_merchants": {
        "question": "Which merchants did I visit repeatedly?",
        "intent": ChatIntent.REPEATED_MERCHANTS.value,
    },
    "concentrated_spending": {
        "question": "Is my spending concentrated in one area?",
        "intent": ChatIntent.CONCENTRATED_SPENDING.value,
    },

    # Anomaly detection
    "anomaly_check": {
        "question": "Did I have unusual spending?",
        "intent": ChatIntent.ANOMALY_CHECK.value,
    },

    # Forecasting and recurring expense features
    "recurring_expenses": {
        "question": "Do I have recurring expenses or subscriptions?",
        "intent": ChatIntent.RECURRING_EXPENSES.value,
    },
    "cashflow_forecast": {
        "question": "Can you forecast my upcoming cashflow?",
        "intent": ChatIntent.CASHFLOW_FORECAST.value,
    },

    # Budget recommendation
    "budget_recommendation": {
        "question": "Where can I reduce my spending?",
        "intent": ChatIntent.BUDGET_RECOMMENDATION.value,
    },
}


def get_available_questions() -> List[Dict[str, str]]:
    """
    Returns the predefined chatbot questions that the UI can display as buttons.
    """

    return [
        {
            "question_id": question_id,
            "question": data["question"],
            "intent": data["intent"],
        }
        for question_id, data in PREDEFINED_QUESTIONS.items()
    ]


def get_intent_from_question_id(question_id: Optional[str]) -> ChatIntent:
    """
    Maps a predefined question_id to a controlled chatbot intent.
    """

    if not question_id:
        return ChatIntent.UNSUPPORTED

    question_data = PREDEFINED_QUESTIONS.get(question_id)

    if not question_data:
        return ChatIntent.UNSUPPORTED

    return ChatIntent(question_data["intent"])


def get_question_text_from_id(question_id: Optional[str]) -> Optional[str]:
    """
    Returns the human-readable predefined question text.
    Used so OpenAI receives the real question even when the user clicked a button.
    """

    if not question_id:
        return None

    question_data = PREDEFINED_QUESTIONS.get(question_id)

    if not question_data:
        return None

    return question_data["question"]