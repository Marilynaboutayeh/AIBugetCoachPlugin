from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.models.transaction import Transaction
from app.services.insights.anomaly.detector import detect_anomalies


def _safe_merchant(tx: Transaction) -> str:
    """
    Return raw merchant description for display.
    """
    return tx.merchant_description or "Unknown"


def _safe_merchant_token(tx: Transaction) -> str:
    """
    Return normalized merchant token for grouping.
    Falls back to merchant_description if merchant_token is missing.
    """
    token = getattr(tx, "merchant_token", None)

    if token and str(token).strip():
        return str(token).strip().lower()

    merchant = getattr(tx, "merchant_description", None)

    if merchant and str(merchant).strip():
        return str(merchant).strip().lower()

    return "unknown"

def build_specific_anomaly_summary(
    anomalies: List[Dict[str, Any]],
    period_label: str,
) -> Optional[str]:
    """
    Build a specific human-readable anomaly insight using the already detected anomalies.
    This does not detect anomalies again; it only formats the existing anomaly results.
    """
    if not anomalies:
        return None

    anomaly_count = len(anomalies)
    first_anomaly = anomalies[0]

    anomaly_type = first_anomaly.get("anomaly_type")
    merchant = first_anomaly.get("merchant", "unknown merchant")
    category = first_anomaly.get("category", "unknown category")
    amount = first_anomaly.get("amount", "unknown amount")
    threshold = first_anomaly.get("threshold")
    matched_transaction_id = first_anomaly.get("matched_transaction_id")
    time_window_minutes = first_anomaly.get("time_window_minutes")
    severity = first_anomaly.get("severity", "unknown")

    if anomaly_type == "duplicate_charge":
        detail = (
            f"a possible duplicate charge was found at {merchant} for {amount} USD. "
            f"It matched another transaction with the same merchant and amount"
        )

        if time_window_minutes is not None:
            detail += f" within {time_window_minutes} minutes"

        if matched_transaction_id:
            detail += f" (matched transaction: {matched_transaction_id})"

        detail += "."

    elif anomaly_type == "global_amount":
        detail = (
            f"a high-value transaction was found at {merchant} for {amount} USD. "
            f"This is higher than the user's normal historical spending"
        )

        if threshold is not None:
            detail += f" threshold of {threshold} USD"

        detail += "."

    elif anomaly_type == "category_amount":
        detail = (
            f"a high-value transaction was found at {merchant} for {amount} USD "
            f"in the category '{category}'. "
            f"This is higher than the user's usual spending in this category"
        )

        if threshold is not None:
            detail += f", where the threshold is {threshold} USD"

        detail += "."

    else:
        message = first_anomaly.get("message", "An unusual transaction was detected.")
        detail = message

    if anomaly_count == 1:
        return (
            f"1 unusual transaction was detected during {period_label} "
            f"with {severity} severity: {detail}"
        )

    return (
        f"{anomaly_count} unusual transactions were detected during {period_label}. "
        f"One example with {severity} severity is: {detail}"
    )

def generate_insights_from_transactions(
    txs: List[Transaction],
    period: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    total_spent = 0.0
    total_income = 0.0

    spending_by_category: Dict[str, float] = {}

    
    spending_by_merchant: Dict[str, Dict[str, Any]] = {}
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

    # ---------- anomaly detection ----------
    anomaly_results = detect_anomalies(
        txs=txs,
        start_date=start_current,
        end_date=end_current,
    )

    # ---------- current period summary ----------
    for tx in filtered_txs:
        amount = float(tx.amount or 0.0)
        direction = (tx.direction or "debit").lower()

        if direction == "debit":
            total_spent += amount

            category = tx.predicted_main_category or "Uncategorized"
            spending_by_category[category] = spending_by_category.get(category, 0.0) + amount

            # Use merchant_token for grouping, raw merchant_description for display
            merchant_token = _safe_merchant_token(tx)
            display_merchant = _safe_merchant(tx)

            if merchant_token not in spending_by_merchant:
                spending_by_merchant[merchant_token] = {
                    "merchant_token": merchant_token,
                    "merchant": display_merchant,
                    "amount": 0.0,
                }

            spending_by_merchant[merchant_token]["amount"] += amount

            current_period_merchant_counts[merchant_token] = (
                current_period_merchant_counts.get(merchant_token, 0) + 1
            )

        elif direction == "credit":
            total_income += amount

    # ---------- previous period spending ----------
    for tx in previous_filtered_txs:
        amount = float(tx.amount or 0.0)
        direction = (tx.direction or "debit").lower()

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
    top_merchants = sorted(
        spending_by_merchant.values(),
        key=lambda x: x["amount"],
        reverse=True
    )[:5]

    insights_text: List[str] = []

    # ---------- 1) spending trend insight ----------
    if period in ("weekly", "monthly", "custom"):
        if previous_period_spending > 0:
            change_percent = (
                (current_period_spending - previous_period_spending)
                / previous_period_spending
            ) * 100

            if current_period_spending > previous_period_spending:
                insights_text.append(
                    f"Your spending during {period_label} has increased by {abs(change_percent):.0f}% compared to {previous_period_label}."
                )
            elif current_period_spending < previous_period_spending:
                insights_text.append(
                    f"Your spending during {period_label} has decreased by {abs(change_percent):.0f}% compared to {previous_period_label}."
                )
            else:
                insights_text.append(
                    f"Your spending during {period_label} is the same as {previous_period_label}."
                )

        elif previous_period_spending == 0 and current_period_spending > 0:
            insights_text.append(
                f"You spent money during {period_label}, while no spending was recorded in {previous_period_label}."
            )

        elif previous_period_spending == 0 and current_period_spending == 0:
            insights_text.append(
                f"No spending was recorded during {period_label}."
            )

    # ---------- 2) repeated merchant insight ----------
    repeated_merchants = [
        merchant_token
        for merchant_token, count in current_period_merchant_counts.items()
        if count >= 2
    ]

    if repeated_merchants:
        repeated_merchant_token = repeated_merchants[0]
        # repeated_merchant_name = spending_by_merchant[repeated_merchant_token]["merchant"]

        insights_text.append(
            f"You made multiple purchases at {repeated_merchant_token} during {period_label}."
        )

    # ---------- 3) spending concentration insight ----------
    if top_merchants and total_spent > 0:
        top_merchant = top_merchants[0]
        # top_merchant_name = top_merchant["merchant"]
        top_merchant_name = top_merchant["merchant_token"]
        top_merchant_amount = top_merchant["amount"]

        concentration_ratio = top_merchant_amount / total_spent

        if concentration_ratio >= 0.4:
            insights_text.append(
                f"A significant portion of your spending during {period_label} is concentrated at {top_merchant_name}."
            )

    # ---------- 4) top category insight ----------
    if top_category and top_category_amount > 0:
        insights_text.append(
            f"Your highest spending category during {period_label} is {top_category} with a total of {round(top_category_amount, 2)}."
        )

    # ---------- 5) optional income insight ----------
    if total_income > 0:
        if total_spent > total_income:
            insights_text.append(
                f"Your spending during {period_label} is higher than your income for the same period."
            )
        elif total_spent < total_income:
            insights_text.append(
                f"Your income during {period_label} is higher than your spending."
            )
        else:
            insights_text.append(
                f"Your income and spending during {period_label} are equal."
            )

    # ---------- 6) anomaly insight ----------
    # if anomaly_results["anomaly_count"] > 0:
    #     insights_text.append(
    #         f"{anomaly_results['anomaly_count']} unusual spending transaction(s) were detected during {period_label}."
    #     )

    # ---------- 6) anomaly insight ----------
    anomaly_summary = build_specific_anomaly_summary(
        anomalies=anomaly_results["anomalies"],
        period_label=period_label,
    )

    if anomaly_summary:
        insights_text.append(anomaly_summary)

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
            {
                "merchant_token": merchant["merchant_token"],
                "merchant": merchant["merchant"],
                "amount": round(merchant["amount"], 2),
            }
            for merchant in top_merchants
        ],
        "anomaly_count": anomaly_results["anomaly_count"],
        "anomalies": anomaly_results["anomalies"],
        "insights_text": insights_text,
    }