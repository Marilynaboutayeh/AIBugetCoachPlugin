from datetime import datetime

from app.services.insights.anomaly.detector import detect_anomalies


class MockTransaction:
    def __init__(
        self,
        amount,
        direction="debit",
        timestamp=None,
        predicted_main_category=None,
        merchant_description=None,
        transaction_id=None,
    ):
        self.amount = amount
        self.direction = direction
        self.timestamp = timestamp
        self.predicted_main_category = predicted_main_category
        self.merchant_description = merchant_description
        self.transaction_id = transaction_id


txs = [
    # Historical transactions before current period
    MockTransaction(20, "debit", datetime(2026, 4, 1, 10, 0), "Groceries", "Carrefour", "tx1"),
    MockTransaction(25, "debit", datetime(2026, 4, 2, 12, 0), "Groceries", "Spinneys", "tx2"),
    MockTransaction(18, "debit", datetime(2026, 4, 3, 14, 0), "Groceries", "Carrefour", "tx3"),
    MockTransaction(30, "debit", datetime(2026, 4, 4, 16, 0), "Shopping", "Zara", "tx4"),
    MockTransaction(22, "debit", datetime(2026, 4, 5, 18, 0), "Groceries", "Le Charcutier", "tx5"),
    MockTransaction(27, "debit", datetime(2026, 4, 6, 13, 0), "Groceries", "Spinneys", "tx6"),
    MockTransaction(35, "debit", datetime(2026, 4, 7, 15, 0), "Shopping", "Pull&Bear", "tx7"),

    # Current period transactions
    MockTransaction(24, "debit", datetime(2026, 4, 20, 10, 0), "Groceries", "Carrefour", "tx8"),
    MockTransaction(250, "debit", datetime(2026, 4, 21, 11, 0), "Shopping", "Zara", "tx9"),
]

result = detect_anomalies(
    txs=txs,
    start_date=datetime(2026, 4, 20, 0, 0),
    end_date=datetime(2026, 4, 23, 23, 59),
)

print("Anomaly count:", result["anomaly_count"])
print("Current period transaction count:", result["current_period_transaction_count"])
print("Historical baseline transaction count:", result["historical_baseline_transaction_count"])
print("\nDetected anomalies:")

for anomaly in result["anomalies"]:
    print(anomaly)