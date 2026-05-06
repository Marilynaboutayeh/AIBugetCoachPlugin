import csv
from typing import List

from app.models.transaction import Transaction


def build_subscription_dataset(
    recurring_candidates: List[dict],
    output_file: str = "subscription_training_dataset.csv",
):
    rows = []

    for candidate in recurring_candidates:
        transactions = candidate["transactions"]

        amounts = [float(tx.amount) for tx in transactions]
        days = [tx.timestamp.day for tx in transactions]

        avg_amount = sum(amounts) / len(amounts)
        amount_variation = max(amounts) - min(amounts)
        day_variation = max(days) - min(days)

        first_transaction = transactions[0]

        rows.append(
            {
                "merchant_description": first_transaction.merchant_description,
                "merchant_token": first_transaction.merchant_token,
                "mcc": first_transaction.mcc,
                "category": first_transaction.predicted_main_category,
                "avg_amount": round(avg_amount, 2),
                "amount_variation": round(amount_variation, 2),
                "day_variation": day_variation,
                "months_count": len(transactions),
                "label": "",   # manual later
            }
        )

    fieldnames = [
        "merchant_description",
        "merchant_token",
        "mcc",
        "category",
        "avg_amount",
        "amount_variation",
        "day_variation",
        "months_count",
        "label",
    ]

    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return output_file