from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Optional

from app.models.transaction import Transaction


def generate_insights_from_transactions(
    txs: List[Transaction],
    period: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    total_spent = 0.0
    total_income = 0.0

    spending_by_category: Dict[str, float] = {}
    spending_by_merchant: Dict[str, float] = {}
    current_period_merchant_counts: Dict[str, int] = {}

    current_period_spending = 0.0
    previous_period_spending = 0.0

    now = datetime.now()

    # ---------- period setup ----------
    if period == "weekly":
        period_label = "this week"
        previous_period_label = "the same period last week"

        start_current = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_current = now

        range_duration = end_current - start_current
        start_previous = start_current - timedelta(days=7)
        end_previous = start_previous + range_duration

    elif period == "monthly":
        period_label = "this month"
        previous_period_label = "the same period last month"

        start_current = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_current = now

        if now.month == 1:
            previous_month = 12
            previous_year = now.year - 1
        else:
            previous_month = now.month - 1
            previous_year = now.year

        start_previous = start_current.replace(year=previous_year, month=previous_month)

        try:
            end_previous = now.replace(year=previous_year, month=previous_month)
        except ValueError:
            temp = now.replace(year=previous_year, month=previous_month, day=1)
            next_month = (temp.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_previous = next_month - timedelta(days=1)

    elif period == "custom" and start_date and end_date:
        period_label = "the selected period"
        previous_period_label = "the previous comparable period"

        start_current = start_date
        end_current = end_date

        range_duration = end_current - start_current
        end_previous = start_current - timedelta(seconds=1)
        start_previous = end_previous - range_duration

    else:
        period_label = "all time"
        previous_period_label = "the previous comparable period"
        start_current = None
        end_current = None
        start_previous = None
        end_previous = None

    # ---------- filtering ----------
    if period in ("weekly", "monthly", "custom") and start_current and end_current:
        filtered_txs = [
            tx for tx in txs
            if tx.timestamp and start_current <= tx.timestamp <= end_current
        ]

        previous_filtered_txs = [
            tx for tx in txs
            if tx.timestamp and start_previous <= tx.timestamp <= end_previous
        ]
    else:
        filtered_txs = txs
        previous_filtered_txs = []

    # ---------- current period summary ----------
    for tx in filtered_txs:
        amount = float(tx.amount or 0.0)
        direction = tx.direction or "debit"

        if direction == "debit":
            total_spent += amount

            category = tx.predicted_main_category or "Uncategorized"
            spending_by_category[category] = spending_by_category.get(category, 0.0) + amount

            merchant = tx.merchant_description or "Unknown"
            spending_by_merchant[merchant] = spending_by_merchant.get(merchant, 0.0) + amount
            current_period_merchant_counts[merchant] = (
                current_period_merchant_counts.get(merchant, 0) + 1
            )

        elif direction == "credit":
            total_income += amount

    # ---------- previous period spending ----------
    for tx in previous_filtered_txs:
        amount = float(tx.amount or 0.0)
        direction = tx.direction or "debit"

        if direction == "debit":
            previous_period_spending += amount

    current_period_spending = total_spent

    # ---------- top category ----------
    top_category = None
    top_category_amount = 0.0
    if spending_by_category:
        top_category, top_category_amount = max(
            spending_by_category.items(),
            key=lambda x: x[1]
        )

    # ---------- top merchants ----------
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
            f"Your spending during {period_label} has increased by {abs(change_percent):.0f}% compared to {previous_period_label}."
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
            f"You made multiple purchases at {repeated_merchant} during {period_label}."
        )

    # 3) Spending concentration alert
    if top_merchants and total_spent > 0:
        top_merchant_name, top_merchant_amount = top_merchants[0]
        concentration_ratio = top_merchant_amount / total_spent

        if concentration_ratio >= 0.4:
            insights_text.append(
                f"A significant portion of your spending during {period_label} is concentrated at {top_merchant_name}."
            )

    return {
        "period": period,
        "start_date": start_current.isoformat() if start_current else None,
        "end_date": end_current.isoformat() if end_current else None,
        "transaction_count": len(filtered_txs),
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