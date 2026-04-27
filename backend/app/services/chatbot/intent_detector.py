from enum import Enum
from typing import Optional


class ChatIntent(str, Enum):
    SPENDING_SUMMARY = "spending_summary"
    CATEGORY_BREAKDOWN = "category_breakdown"
    TOP_CATEGORY = "top_category"
    SPENDING_COMPARISON = "spending_comparison"
    ANOMALY_CHECK = "anomaly_check"
    BUDGET_RECOMMENDATION = "budget_recommendation"
    UNSUPPORTED = "unsupported"


def detect_intent_from_text(question: Optional[str]) -> ChatIntent:
    """
    Optional fallback intent detection for free-text questions.

    Main chatbot flow should use predefined question_id.
    This function is only used when question_id is missing.
    """

    if not question:
        return ChatIntent.UNSUPPORTED

    q = question.lower().strip()

    spending_words = [
        "spend", "spent", "spending", "expense", "expenses", "money", "total"
    ]

    category_words = [
        "category", "categories", "groceries", "shopping", "clothing",
        "restaurants", "food", "transport", "health"
    ]

    anomaly_words = [
        "unusual", "abnormal", "anomaly", "strange", "weird", "suspicious"
    ]

    comparison_words = [
        "higher", "lower", "increase", "decrease", "compare", "compared",
        "last month", "previous", "difference", "changed"
    ]

    recommendation_words = [
        "reduce", "save", "saving", "cut", "improve", "recommend",
        "advice", "budget"
    ]

    # These are intentionally unsupported for now because recurring expenses
    # and cashflow forecasting are not implemented yet.
    recurring_words = [
        "recurring", "subscription", "subscriptions",
        "monthly payment", "regular payment"
    ]

    forecast_words = [
        "forecast", "predict", "prediction", "next month",
        "next week", "future", "cashflow"
    ]

    if any(word in q for word in recurring_words):
        return ChatIntent.UNSUPPORTED

    if any(word in q for word in forecast_words):
        return ChatIntent.UNSUPPORTED

    if any(word in q for word in anomaly_words):
        return ChatIntent.ANOMALY_CHECK

    if any(word in q for word in comparison_words):
        return ChatIntent.SPENDING_COMPARISON

    if any(word in q for word in recommendation_words):
        return ChatIntent.BUDGET_RECOMMENDATION

    if "top" in q or "most" in q or "highest" in q or "where did my money go" in q:
        return ChatIntent.TOP_CATEGORY

    if any(word in q for word in category_words):
        return ChatIntent.CATEGORY_BREAKDOWN

    if any(word in q for word in spending_words) or "how much" in q:
        return ChatIntent.SPENDING_SUMMARY

    return ChatIntent.UNSUPPORTED