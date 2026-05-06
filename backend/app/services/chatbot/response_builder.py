from typing import Any, Dict

from app.services.chatbot.intent_detector import ChatIntent


def build_chat_response(intent: ChatIntent, insights: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a controlled chatbot response using only existing insights data.

    This version does not use OpenAI yet.
    It is deterministic, safe, and easy to test.
    """

    if intent == ChatIntent.UNSUPPORTED:
        return {
            "answer": (
                "I can only answer questions based on the financial insights currently available. "
                "For now, you can ask about spending summaries, spending categories, top spending, "
                "spending changes, unusual spending, or simple budget suggestions."
            ),
            "confidence": "high",
            "used_data": {},
            "data_sources": [],
        }

    total_spent = insights.get("total_spent", 0)
    spend_by_category = insights.get("spend_by_category", {})
    top_category = insights.get("top_category")
    anomalies = insights.get("anomalies", [])

    if intent == ChatIntent.SPENDING_SUMMARY:
        return {
            "answer": f"You spent a total of {total_spent} during this period.",
            "confidence": "high",
            "used_data": {
                "total_spent": total_spent,
            },
            "data_sources": ["spending_summary"],
        }

    if intent == ChatIntent.CATEGORY_BREAKDOWN:
        if not spend_by_category:
            answer = "There is not enough category spending data available for this period."
        else:
            parts = [
                f"{category}: {amount}"
                for category, amount in spend_by_category.items()
            ]
            answer = "Your spending by category is: " + ", ".join(parts) + "."

        return {
            "answer": answer,
            "confidence": "high",
            "used_data": {
                "spend_by_category": spend_by_category,
            },
            "data_sources": ["category_breakdown"],
        }

    if intent == ChatIntent.TOP_CATEGORY:
        if isinstance(top_category, dict):
            name = top_category.get("name")
            amount = top_category.get("amount")

            if name is not None and amount is not None:
                answer = f"Your top spending category is {name}, with a total of {amount}."
                used_data = top_category
            else:
                answer = "There is not enough category data to identify your top spending category."
                used_data = {}

        elif spend_by_category:
            name = max(spend_by_category, key=spend_by_category.get)
            amount = spend_by_category[name]
            answer = f"Your top spending category is {name}, with a total of {amount}."
            used_data = {
                "name": name,
                "amount": amount,
            }

        else:
            answer = "There is not enough category data to identify your top spending category."
            used_data = {}

        return {
            "answer": answer,
            "confidence": "high" if used_data else "low",
            "used_data": used_data,
            "data_sources": ["top_category"],
        }

    if intent == ChatIntent.ANOMALY_CHECK:
        if anomalies:
            answer = f"I found {len(anomalies)} unusual spending case(s) in your transactions."
        else:
            answer = "I did not find unusual spending behavior in the available analyzed data."

        return {
            "answer": answer,
            "confidence": "medium",
            "used_data": {
                "anomaly_count": len(anomalies),
                "anomalies": anomalies,
            },
            "data_sources": ["anomaly_detection"],
        }

    if intent == ChatIntent.BUDGET_RECOMMENDATION:
        if spend_by_category:
            name = max(spend_by_category, key=spend_by_category.get)
            amount = spend_by_category[name]

            answer = (
                f"Based on your analyzed spending, the first category to review is {name}, "
                f"because it has the highest spending amount: {amount}."
            )

            used_data = {
                "category": name,
                "amount": amount,
            }
        else:
            answer = "There is not enough spending data to suggest a budget improvement."
            used_data = {}

        return {
            "answer": answer,
            "confidence": "medium" if used_data else "low",
            "used_data": used_data,
            "data_sources": ["budget_recommendation"],
        }

    if intent == ChatIntent.SPENDING_COMPARISON:
        current_total = insights.get("current_total_spent")
        previous_total = insights.get("previous_total_spent")
        change_amount = insights.get("change_amount")
        change_percentage = insights.get("change_percentage")

        if current_total is not None and previous_total is not None:
            if change_percentage is not None:
                answer = (
                    f"Your spending changed from {previous_total} to {current_total}. "
                    f"The difference is {change_amount}, which represents {change_percentage}%."
                )
            else:
                answer = (
                    f"Your spending changed from {previous_total} to {current_total}. "
                    f"The difference is {change_amount}. A percentage change is not available "
                    f"because the previous period spending was zero."
                )

            used_data = {
                "current_total_spent": current_total,
                "previous_total_spent": previous_total,
                "change_amount": change_amount,
                "change_percentage": change_percentage,
            }
        else:
            answer = (
                "I cannot compare your spending because previous-period insight data "
                "is not available in the current response."
            )
            used_data = {}

        return {
            "answer": answer,
            "confidence": "medium" if used_data else "low",
            "used_data": used_data,
            "data_sources": ["spending_comparison"],
        }

    return {
        "answer": "I could not generate an answer from the available analyzed insights.",
        "confidence": "low",
        "used_data": {},
        "data_sources": [],
    }