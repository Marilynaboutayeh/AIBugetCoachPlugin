from collections import Counter
from statistics import mean, stdev
from typing import List
from datetime import datetime

from app.models.transaction import Transaction


def build_forecast_features(transactions: List[Transaction]):
    if len(transactions) < 2:
        return None

    transactions = sorted(transactions, key=lambda x: x.timestamp)

    merchant_token = transactions[0].merchant_token
    mcc = transactions[0].mcc
    main_category = transactions[0].predicted_main_category

    amounts = [t.amount for t in transactions if t.amount is not None]

    amount_avg = mean(amounts)

    amount_std = stdev(amounts) if len(amounts) > 1 else 0

    intervals = []

    for i in range(1, len(transactions)):
        previous_date = transactions[i - 1].timestamp
        current_date = transactions[i].timestamp

        days_diff = (current_date - previous_date).days
        intervals.append(days_diff)

    interval_avg_days = mean(intervals)

    interval_std_days = stdev(intervals) if len(intervals) > 1 else 0

    occurrence_count = len(transactions)

    directions = [t.direction for t in transactions if t.direction]

    most_common_direction_count = Counter(directions).most_common(1)[0][1]

    same_direction_ratio = most_common_direction_count / len(directions)

    return {
        "merchant_token": merchant_token,
        "mcc": mcc,
        "main_category": main_category,
        "amount_avg": amount_avg,
        "amount_std": amount_std,
        "interval_avg_days": interval_avg_days,
        "interval_std_days": interval_std_days,
        "occurrence_count": occurrence_count,
        "same_direction_ratio": same_direction_ratio,
    }