from datetime import datetime
from typing import Any, Dict, List

from app.models.transaction import Transaction


AMOUNT_TOLERANCE = 0.05  # 5%
DAY_TOLERANCE = 3       # +/- 3 days


def is_amount_similar(amount1: float, amount2: float) -> bool:
    if amount1 <= 0 or amount2 <= 0:
        return False

    difference_ratio = abs(amount1 - amount2) / amount1
    return difference_ratio <= AMOUNT_TOLERANCE


def is_day_similar(day1: int, day2: int) -> bool:
    return abs(day1 - day2) <= DAY_TOLERANCE


def detect_recurring_candidates(txs: List[Transaction]) -> List[Dict[str, Any]]:
    transactions_by_merchant: Dict[str, List[Transaction]] = {}

    for tx in txs:
        if tx.direction != "debit":
            continue

        if not tx.timestamp or not tx.amount or not tx.merchant_description:
            continue

        merchant = tx.merchant_description.strip().lower()

        if merchant not in transactions_by_merchant:
            transactions_by_merchant[merchant] = []

        transactions_by_merchant[merchant].append(tx)

    recurring_candidates: List[Dict[str, Any]] = []

    for merchant, merchant_txs in transactions_by_merchant.items():
        merchant_txs.sort(key=lambda tx: tx.timestamp)

        if len(merchant_txs) < 2:
            continue

        first_tx = merchant_txs[0]
        similar_transactions = [first_tx]

        for tx in merchant_txs[1:]:
            same_amount = is_amount_similar(float(first_tx.amount), float(tx.amount))
            same_day = is_day_similar(first_tx.timestamp.day, tx.timestamp.day)

            different_month = (
                first_tx.timestamp.year != tx.timestamp.year
                or first_tx.timestamp.month != tx.timestamp.month
            )

            if same_amount and same_day and different_month:
                similar_transactions.append(tx)

        if len(similar_transactions) >= 2:
            average_amount = sum(float(tx.amount) for tx in similar_transactions) / len(similar_transactions)
            last_transaction = similar_transactions[-1]

            recurring_candidates.append(
                {
                    "merchant": last_transaction.merchant_description,
                    "frequency": "monthly_candidate",
                    "matched_transactions": len(similar_transactions),
                    "average_amount": round(average_amount, 2),
                    "last_transaction_date": last_transaction.timestamp.date().isoformat(),
                    "transactions": similar_transactions,
                }
            )

    return recurring_candidates