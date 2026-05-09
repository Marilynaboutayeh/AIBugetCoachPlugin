from typing import Any, Dict, List

from app.services.chatbot.intent_detector import ChatIntent


def _format_amount(value: Any) -> str:
    """
    Safely formats numeric amounts.
    Keeps the chatbot from crashing if a value is missing or not numeric.
    """
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def _get_first_available(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """
    Returns the first available non-empty value from a dictionary.
    Useful because service outputs may use slightly different key names.
    """
    for key in keys:
        value = data.get(key)
        if value is not None:
            return value
    return default


def build_chat_response(intent: ChatIntent, insights: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a controlled chatbot response using only backend-generated insight/forecast data.

    This function does not calculate new financial insights.
    It only formats existing results from the insight engine, recurring service,
    forecast service, and anomaly detection logic.
    """

    if intent == ChatIntent.UNSUPPORTED:
        return {
            "answer": (
                "I can only answer questions based on the financial insights currently available. "
                "You can ask about spending summaries, categories, top spending, merchants, "
                "spending changes, unusual spending, recurring expenses, forecasts, or budget suggestions."
            ),
            "confidence": "high",
            "used_data": {},
            "data_sources": [],
        }

    total_spent = insights.get("total_spent", 0)
    spend_by_category = insights.get("spend_by_category", {})
    top_category = insights.get("top_category")
    anomalies = insights.get("anomalies", [])

    top_merchants = (
        insights.get("top_merchants_by_spend")
        or insights.get("top_merchants")
        or []
    )

    repeated_merchants = insights.get("repeated_merchants", [])
    concentrated_spending = insights.get("concentrated_spending")

    recurring_candidates = (
        insights.get("recurring_candidates")
        or insights.get("recurring_expenses")
        or []
    )

    cashflow_forecast = (
        insights.get("cashflow_forecast")
        or insights.get("forecast")
        or insights.get("forecast_result")
    )

    if intent == ChatIntent.SPENDING_SUMMARY:
        return {
            "answer": f"You spent a total of {_format_amount(total_spent)} during this period.",
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
                f"{category}: {_format_amount(amount)}"
                for category, amount in spend_by_category.items()
            ]
            answer = "Your spending by category is: " + ", ".join(parts) + "."

        return {
            "answer": answer,
            "confidence": "high" if spend_by_category else "low",
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
                answer = (
                    f"Your top spending category is {name}, "
                    f"with a total of {_format_amount(amount)}."
                )
                used_data = top_category
            else:
                answer = "There is not enough category data to identify your top spending category."
                used_data = {}

        elif spend_by_category:
            name = max(spend_by_category, key=spend_by_category.get)
            amount = spend_by_category[name]
            answer = (
                f"Your top spending category is {name}, "
                f"with a total of {_format_amount(amount)}."
            )
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

    if intent == ChatIntent.SPENDING_COMPARISON:
        current_total = insights.get("current_total_spent")
        previous_total = insights.get("previous_total_spent")
        change_amount = insights.get("change_amount")
        change_percentage = insights.get("change_percentage")

        if current_total is not None and previous_total is not None:
            if change_percentage is not None:
                answer = (
                    f"Your spending changed from {_format_amount(previous_total)} "
                    f"to {_format_amount(current_total)}. "
                    f"The difference is {_format_amount(change_amount)}, "
                    f"which represents {_format_amount(change_percentage)}%."
                )
            else:
                answer = (
                    f"Your spending changed from {_format_amount(previous_total)} "
                    f"to {_format_amount(current_total)}. "
                    f"The difference is {_format_amount(change_amount)}. "
                    "A percentage change is not available because the previous period spending was zero."
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

    if intent == ChatIntent.TOP_MERCHANTS:
        if not top_merchants:
            return {
                "answer": "There is not enough merchant spending data available for this period.",
                "confidence": "low",
                "used_data": {
                    "top_merchants_by_spend": [],
                },
                "data_sources": ["top_merchants"],
            }

        parts = []
        for merchant in top_merchants[:3]:
            if isinstance(merchant, dict):
                name = _get_first_available(
                    merchant,
                    ["merchant", "merchant_token", "merchant_description", "name"],
                    "Unknown merchant",
                )
                amount = _get_first_available(
                    merchant,
                    ["amount", "total_amount", "total_spent"],
                    0,
                )
                parts.append(f"{name}: {_format_amount(amount)}")
            else:
                parts.append(str(merchant))

        return {
            "answer": "Your top merchants are: " + ", ".join(parts) + ".",
            "confidence": "high",
            "used_data": {
                "top_merchants_by_spend": top_merchants,
            },
            "data_sources": ["top_merchants"],
        }

    if intent == ChatIntent.REPEATED_MERCHANTS:
        if not repeated_merchants:
            return {
                "answer": "No repeated merchant pattern was detected in the available analyzed data.",
                "confidence": "medium",
                "used_data": {
                    "repeated_merchants": [],
                },
                "data_sources": ["repeated_merchants"],
            }

        parts = []
        for merchant in repeated_merchants[:3]:
            if isinstance(merchant, dict):
                name = _get_first_available(
                    merchant,
                    ["merchant", "merchant_token", "merchant_description", "name"],
                    "Unknown merchant",
                )
                count = _get_first_available(
                    merchant,
                    ["transaction_count", "count", "occurrence_count"],
                    0,
                )
                total = _get_first_available(
                    merchant,
                    ["total_amount", "amount", "total_spent"],
                    0,
                )
                parts.append(
                    f"{name} appeared {count} times, totaling {_format_amount(total)}"
                )
            else:
                parts.append(str(merchant))

        return {
            "answer": "Repeated merchant activity detected: " + ", ".join(parts) + ".",
            "confidence": "medium",
            "used_data": {
                "repeated_merchants": repeated_merchants,
            },
            "data_sources": ["repeated_merchants"],
        }

    if intent == ChatIntent.CONCENTRATED_SPENDING:
        if not concentrated_spending:
            return {
                "answer": "No strong spending concentration was detected in the available analyzed data.",
                "confidence": "medium",
                "used_data": {
                    "concentrated_spending": None,
                },
                "data_sources": ["concentrated_spending"],
            }

        if isinstance(concentrated_spending, dict):
            category = _get_first_available(
                concentrated_spending,
                ["category", "name", "top_category"],
            )
            merchant = _get_first_available(
                concentrated_spending,
                ["merchant", "merchant_token", "top_merchant"],
            )
            percentage = _get_first_available(
                concentrated_spending,
                ["percentage", "share", "concentration_percentage"],
            )
            amount = _get_first_available(
                concentrated_spending,
                ["amount", "total_amount", "total_spent"],
            )

            if category and percentage is not None:
                answer = (
                    f"Your spending is concentrated in {category}, "
                    f"which represents {_format_amount(percentage)}% of the analyzed spending."
                )
            elif merchant and percentage is not None:
                answer = (
                    f"Your spending is concentrated at {merchant}, "
                    f"which represents {_format_amount(percentage)}% of the analyzed spending."
                )
            elif category and amount is not None:
                answer = (
                    f"Your spending is concentrated in {category}, "
                    f"with a total of {_format_amount(amount)}."
                )
            else:
                answer = str(concentrated_spending)
        else:
            answer = str(concentrated_spending)

        return {
            "answer": answer,
            "confidence": "medium",
            "used_data": {
                "concentrated_spending": concentrated_spending,
            },
            "data_sources": ["concentrated_spending"],
        }

    if intent == ChatIntent.ANOMALY_CHECK:
        if anomalies:
            first_message = None
            if isinstance(anomalies[0], dict):
                first_message = anomalies[0].get("message")

            if first_message:
                answer = (
                    f"I found {len(anomalies)} unusual spending case(s). "
                    f"Example: {first_message}"
                )
            else:
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

    if intent == ChatIntent.RECURRING_EXPENSES:
        if not recurring_candidates:
            return {
                "answer": "No recurring expenses or subscriptions were detected based on the available transactions.",
                "confidence": "medium",
                "used_data": {
                    "recurring_candidates": [],
                },
                "data_sources": ["recurring_expenses"],
            }

        parts = []
        for item in recurring_candidates[:3]:
            if isinstance(item, dict):
                name = _get_first_available(
                    item,
                    ["merchant_token", "merchant", "merchant_description", "name"],
                    "Unknown merchant",
                )
                amount = _get_first_available(
                    item,
                    ["avg_amount", "average_amount", "amount"],
                    0,
                )
                confidence = item.get("confidence")
                occurrence_count = _get_first_available(
                    item,
                    ["occurrence_count", "matched_transactions", "transaction_count", "count"],
                )

                text = f"{name}, around {_format_amount(amount)} per month"

                if occurrence_count is not None:
                    text += f", detected across {occurrence_count} payments"

                if confidence is not None:
                    text += f", confidence {_format_amount(confidence)}"

                parts.append(text)
            else:
                parts.append(str(item))

        return {
            "answer": "Likely recurring expenses detected: " + "; ".join(parts) + ".",
            "confidence": "medium",
            "used_data": {
                "recurring_candidates": recurring_candidates,
            },
            "data_sources": ["recurring_expenses"],
        }

    if intent == ChatIntent.CASHFLOW_FORECAST:
        if not cashflow_forecast:
            return {
                "answer": "Cashflow forecasting is not available from the analyzed data yet.",
                "confidence": "low",
                "used_data": {
                    "cashflow_forecast": None,
                },
                "data_sources": ["cashflow_forecast"],
            }

        if isinstance(cashflow_forecast, dict):
            forecast_total = _get_first_available(
                cashflow_forecast,
                ["forecast_total", "predicted_total", "expected_total", "amount"],
            )
            forecast_period = _get_first_available(
                cashflow_forecast,
                ["period", "forecast_period", "target_period"],
            )
            confidence = cashflow_forecast.get("confidence")
            message = cashflow_forecast.get("message")

            if message:
                answer = message
            elif forecast_total is not None and forecast_period:
                answer = (
                    f"The forecasted cashflow for {forecast_period} is "
                    f"{_format_amount(forecast_total)}."
                )
            elif forecast_total is not None:
                answer = f"The forecasted cashflow is {_format_amount(forecast_total)}."
            else:
                answer = str(cashflow_forecast)

            if confidence is not None and "confidence" not in answer.lower():
                answer += f" Confidence: {_format_amount(confidence)}."
        else:
            answer = str(cashflow_forecast)

        return {
            "answer": answer,
            "confidence": "medium",
            "used_data": {
                "cashflow_forecast": cashflow_forecast,
            },
            "data_sources": ["cashflow_forecast"],
        }

    if intent == ChatIntent.BUDGET_RECOMMENDATION:
        if spend_by_category:
            name = max(spend_by_category, key=spend_by_category.get)
            amount = spend_by_category[name]

            answer = (
                f"Based on your analyzed spending, the first category to review is {name}, "
                f"because it has the highest spending amount: {_format_amount(amount)}."
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

    return {
        "answer": "I could not generate an answer from the available analyzed insights.",
        "confidence": "low",
        "used_data": {},
        "data_sources": [],
    }