from enum import Enum
from typing import Optional


class ChatIntent(str, Enum):
    SPENDING_SUMMARY = "spending_summary"
    CATEGORY_BREAKDOWN = "category_breakdown"
    TOP_CATEGORY = "top_category"
    SPENDING_COMPARISON = "spending_comparison"

    TOP_MERCHANTS = "top_merchants"
    REPEATED_MERCHANTS = "repeated_merchants"
    CONCENTRATED_SPENDING = "concentrated_spending"

    ANOMALY_CHECK = "anomaly_check"
    RECURRING_EXPENSES = "recurring_expenses"
    CASHFLOW_FORECAST = "cashflow_forecast"

    BUDGET_RECOMMENDATION = "budget_recommendation"
    UNSUPPORTED = "unsupported"


def detect_intent_from_text(question: Optional[str]) -> ChatIntent:
    """
    Fallback intent detection for free-text questions.

    Main chatbot flow can still use predefined question_id.
    This function is used when question_id is missing.
    """

    if not question:
        return ChatIntent.UNSUPPORTED

    q = question.lower().strip()

    recurring_words = [
        "recurring",
        "subscription",
        "subscriptions",
        "monthly payment",
        "monthly payments",
        "regular payment",
        "regular payments",
        "repeated every month",
        "monthly charge",
        "monthly charges",
        "automatic payment",
        "automatic payments",
        "fixed payment",
        "fixed payments",
        "repeat every month",
        "repeats every month",
    ]

    forecast_words = [
        "forecast",
        "predict",
        "prediction",
        "next month",
        "next week",
        "future",
        "cashflow",
        "cash flow",
        "upcoming",
        "upcoming spending",
        "upcoming expenses",
        "expected spending",
        "expected expenses",
        "how much will i spend",
        "will i have enough",
        "future spending",
        "future expenses",
    ]

    anomaly_words = [
        "unusual",
        "abnormal",
        "anomaly",
        "anomalies",
        "strange",
        "weird",
        "suspicious",
        "unexpected",
        "duplicate",
        "double charge",
        "charged twice",
        "unusual spending",
        "suspicious transaction",
    ]

    repeated_merchant_words = [
        "repeated merchant",
        "repeated merchants",
        "same merchant",
        "same place",
        "same store",
        "often",
        "frequently",
        "again and again",
        "visited repeatedly",
        "paid many times",
        "merchant i use most often",
        "merchant i visit most",
    ]

    concentrated_words = [
        "concentrated",
        "too much in one",
        "most of my money",
        "focused in one",
        "main area",
        "one category",
        "one place",
        "one merchant",
        "spending concentration",
        "concentrated spending",
    ]

    top_merchant_words = [
        "top merchant",
        "top merchants",
        "biggest merchant",
        "biggest merchants",
        "highest merchant",
        "highest merchants",
        "where did i spend the most",
        "where did my money go",
        "stores",
        "shops",
        "vendors",
        "places i spent",
        "merchant spending",
        "spending by merchant",
    ]

    comparison_words = [
        "higher",
        "lower",
        "increase",
        "decrease",
        "compare",
        "compared",
        "last month",
        "previous",
        "previous month",
        "difference",
        "changed",
        "more than before",
        "less than before",
        "spending change",
        "did i spend more",
        "did i spend less",
    ]

    recommendation_words = [
        "reduce",
        "save",
        "saving",
        "cut",
        "improve",
        "recommend",
        "advice",
        "budget",
        "budget recommendation",
        "where can i reduce",
        "where can i save",
        "how can i save",
        "how can i reduce",
    ]

    top_category_words = [
        "top category",
        "highest category",
        "biggest category",
        "main category",
        "most expensive category",
        "category spent the most",
        "which category did i spend the most",
        "where is my highest category",
    ]

    category_words = [
        "category",
        "categories",
        "breakdown",
        "distribution",
        "spending by category",
        "category breakdown",
        "groceries",
        "shopping",
        "clothing",
        "restaurants",
        "food",
        "transport",
        "health",
    ]

    spending_words = [
        "spend",
        "spent",
        "spending",
        "expense",
        "expenses",
        "money",
        "total",
        "how much",
        "summary",
        "overview",
        "total spending",
        "spending summary",
    ]

    # Specific intents first.
    # This avoids classifying detailed questions as generic spending/category questions.

    if any(word in q for word in recurring_words):
        return ChatIntent.RECURRING_EXPENSES

    if any(word in q for word in forecast_words):
        return ChatIntent.CASHFLOW_FORECAST

    if any(word in q for word in anomaly_words):
        return ChatIntent.ANOMALY_CHECK

    if any(word in q for word in repeated_merchant_words):
        return ChatIntent.REPEATED_MERCHANTS

    if any(word in q for word in concentrated_words):
        return ChatIntent.CONCENTRATED_SPENDING

    if any(word in q for word in top_merchant_words):
        return ChatIntent.TOP_MERCHANTS

    if any(word in q for word in comparison_words):
        return ChatIntent.SPENDING_COMPARISON

    if any(word in q for word in recommendation_words):
        return ChatIntent.BUDGET_RECOMMENDATION

    if any(word in q for word in top_category_words):
        return ChatIntent.TOP_CATEGORY

    if any(word in q for word in category_words):
        return ChatIntent.CATEGORY_BREAKDOWN

    if any(word in q for word in spending_words):
        return ChatIntent.SPENDING_SUMMARY

    # General fallback for "top / most / highest" questions.
    # If it was about merchants, it would already be caught above.
    if "top" in q or "most" in q or "highest" in q:
        return ChatIntent.TOP_CATEGORY

    return ChatIntent.UNSUPPORTED