from datetime import datetime
from typing import Any, Dict, List, Tuple

from app.models.transaction import Transaction


def generate_insights_from_transactions(txs: List[Transaction]) -> Dict[str, Any]:
    total_spent = 0.0
    total_income = 0.0

    spending_by_category: Dict[str, float] = {}
    spending_by_merchant: Dict[str, float] = {}
    current_period_merchant_counts: Dict[str, int] = {}

    current_period_spending = 0.0
    previous_period_spending = 0.0

    now = datetime.now()
    current_year = now.year
    current_month = now.month
    current_day = now.day

    if current_month == 1:
        previous_month = 12
        previous_month_year = current_year - 1
    else:
        previous_month = current_month - 1
        previous_month_year = current_year

    for tx in txs:
        amount = float(tx.amount or 0.0)
        direction = tx.direction or "debit"

        if direction == "debit":
            total_spent += amount

            category = tx.predicted_main_category or "Uncategorized"
            spending_by_category[category] = spending_by_category.get(category, 0.0) + amount

            merchant = tx.merchant_description or "Unknown"
            spending_by_merchant[merchant] = spending_by_merchant.get(merchant, 0.0) + amount

            if tx.timestamp:
                tx_year = tx.timestamp.year
                tx_month = tx.timestamp.month
                tx_day = tx.timestamp.day

                # Current month -> same period up to today
                if (
                    tx_year == current_year
                    and tx_month == current_month
                    and tx_day <= current_day
                ):
                    current_period_spending += amount
                    current_period_merchant_counts[merchant] = (
                        current_period_merchant_counts.get(merchant, 0) + 1
                    )

                # Previous month -> same period up to same day
                elif (
                    tx_year == previous_month_year
                    and tx_month == previous_month
                    and tx_day <= current_day
                ):
                    previous_period_spending += amount

        elif direction == "credit":
            total_income += amount

    top_category = None
    top_category_amount = 0.0
    if spending_by_category:
        top_category, top_category_amount = max(
            spending_by_category.items(),
            key=lambda x: x[1]
        )

    top_merchants: List[Tuple[str, float]] = sorted(
        spending_by_merchant.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    insights_text: List[str] = []

    # 1) Spending increase alert
    if previous_period_spending > 0 and current_period_spending > previous_period_spending:
        change_percent = (
            (current_period_spending - previous_period_spending)
            / previous_period_spending
        ) * 100

        insights_text.append(
            f"Your spending this month has increased by {abs(change_percent):.0f}% compared to the same period last month."
        )

    # 2) Repeated merchant alert
    repeated_merchants = [
        merchant
        for merchant, count in current_period_merchant_counts.items()
        if count >= 2
    ]

    if repeated_merchants:
        repeated_merchant = repeated_merchants[0]
        insights_text.append(
            f"You made multiple purchases at {repeated_merchant} this month."
        )

    # 3) Spending concentration alert
    if top_merchants and total_spent > 0:
        top_merchant_name, top_merchant_amount = top_merchants[0]
        concentration_ratio = top_merchant_amount / total_spent

        if concentration_ratio >= 0.4:
            insights_text.append(
                f"A significant portion of your spending is concentrated at {top_merchant_name}."
            )

    return {
        "transaction_count": len(txs),
        "total_spent": round(total_spent, 2),
        "total_income": round(total_income, 2),
        "spend_by_category": {
            category: round(amount, 2)
            for category, amount in spending_by_category.items()
        },
        "top_category": {
            "name": top_category,
            "amount": round(top_category_amount, 2)
        } if top_category else None,
        "top_merchants_by_spend": [
            {"merchant": merchant, "amount": round(amount, 2)}
            for merchant, amount in top_merchants
        ],
        "insights_text": insights_text,
    }