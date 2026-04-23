from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.models.transaction import Transaction


def _safe_amount(tx: Transaction) -> float:
    """Return transaction amount as float, defaulting to 0.0."""
    try:
        return float(tx.amount or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _safe_direction(tx: Transaction) -> str:
    """Return normalized transaction direction."""
    return (tx.direction or "debit").strip().lower()


def _safe_category(tx: Transaction) -> str:
    """Return normalized category or fallback."""
    return tx.predicted_main_category or "Uncategorized"


def _safe_merchant(tx: Transaction) -> str:
    """Return merchant description or fallback."""
    return tx.merchant_description or "Unknown"


def _safe_transaction_id(tx: Transaction) -> Optional[str]:
    """Return transaction id if present."""
    return getattr(tx, "transaction_id", None)


def get_valid_debit_transactions(txs: List[Transaction]) -> List[Transaction]:
    """
    Keep only valid debit transactions with a positive amount.
    """
    valid: List[Transaction] = []

    for tx in txs:
        amount = _safe_amount(tx)
        direction = _safe_direction(tx)

        if direction == "debit" and amount > 0:
            valid.append(tx)

    return valid


def split_current_and_historical_transactions(
    txs: List[Transaction],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Tuple[List[Transaction], List[Transaction]]:
    """
    Split transactions into:
    - current period transactions: between start_date and end_date
    - historical baseline transactions: before start_date

    If no valid dates are provided, all transactions are treated as current
    and historical is empty.
    """
    if not start_date or not end_date:
        return txs, []

    current_period: List[Transaction] = []
    historical_period: List[Transaction] = []

    for tx in txs:
        if not tx.timestamp:
            continue

        if start_date <= tx.timestamp <= end_date:
            current_period.append(tx)
        elif tx.timestamp < start_date:
            historical_period.append(tx)

    return current_period, historical_period


def _median(values: List[float]) -> float:
    """
    Compute median of a sorted list.
    """
    n = len(values)
    if n == 0:
        return 0.0

    mid = n // 2

    if n % 2 == 0:
        return (values[mid - 1] + values[mid]) / 2.0

    return values[mid]


def _quartiles(values: List[float]) -> Tuple[float, float]:
    """
    Compute Q1 and Q3 using the median-of-halves method.
    Assumes input is non-empty.
    """
    sorted_values = sorted(values)
    n = len(sorted_values)
    mid = n // 2

    if n % 2 == 0:
        lower_half = sorted_values[:mid]
        upper_half = sorted_values[mid:]
    else:
        lower_half = sorted_values[:mid]
        upper_half = sorted_values[mid + 1:]

    q1 = _median(lower_half) if lower_half else sorted_values[0]
    q3 = _median(upper_half) if upper_half else sorted_values[-1]

    return q1, q3


def compute_iqr_threshold(amounts: List[float]) -> Optional[float]:
    """
    Compute upper anomaly threshold using:
        Q3 + 1.5 * IQR

    Returns None if there is not enough data.
    """
    cleaned = [a for a in amounts if a > 0]

    if len(cleaned) < 4:
        return None

    q1, q3 = _quartiles(cleaned)
    iqr = q3 - q1

    return q3 + (1.5 * iqr)


def detect_global_amount_anomalies(
    current_txs: List[Transaction],
    historical_txs: List[Transaction],
) -> List[Dict[str, Any]]:
    """
    Detect transactions in the current period whose amount is unusually high
    compared to the user's historical debit spending overall.
    """
    anomalies: List[Dict[str, Any]] = []

    historical_amounts = [_safe_amount(tx) for tx in historical_txs if _safe_amount(tx) > 0]

    # Minimum history required to build a baseline
    if len(historical_amounts) < 5:
        return anomalies

    threshold = compute_iqr_threshold(historical_amounts)
    if threshold is None:
        return anomalies

    for tx in current_txs:
        amount = _safe_amount(tx)

        if amount > threshold:
            anomalies.append(
                {
                    "anomaly_type": "global_amount",
                    "severity": "high",
                    "transaction_id": _safe_transaction_id(tx),
                    "merchant": _safe_merchant(tx),
                    "category": _safe_category(tx),
                    "amount": round(amount, 2),
                    "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                    "message": (
                        "This transaction is unusually high compared to the user's "
                        "normal historical spending."
                    ),
                    "threshold": round(threshold, 2),
                }
            )

    return anomalies


def detect_category_amount_anomalies(
    current_txs: List[Transaction],
    historical_txs: List[Transaction],
) -> List[Dict[str, Any]]:
    """
    Detect transactions in the current period whose amount is unusually high
    compared to the user's historical spending in the same category.
    """
    anomalies: List[Dict[str, Any]] = []

    # Build category -> historical amounts
    historical_by_category: Dict[str, List[float]] = {}

    for tx in historical_txs:
        category = _safe_category(tx)
        amount = _safe_amount(tx)

        if amount > 0:
            historical_by_category.setdefault(category, []).append(amount)

    for tx in current_txs:
        category = _safe_category(tx)
        amount = _safe_amount(tx)

        category_history = historical_by_category.get(category, [])

        # Minimum history required inside the category
        if len(category_history) < 3:
            continue

        threshold = compute_iqr_threshold(category_history)
        if threshold is None:
            continue

        if amount > threshold:
            anomalies.append(
                {
                    "anomaly_type": "category_amount",
                    "severity": "medium",
                    "transaction_id": _safe_transaction_id(tx),
                    "merchant": _safe_merchant(tx),
                    "category": category,
                    "amount": round(amount, 2),
                    "timestamp": tx.timestamp.isoformat() if tx.timestamp else None,
                    "message": (
                        f"This transaction is unusually high compared to the user's "
                        f"usual spending in category '{category}'."
                    ),
                    "threshold": round(threshold, 2),
                }
            )

    return anomalies


def detect_anomalies(
    txs: List[Transaction],
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Main entry point for anomaly detection.

    Flow:
    1. keep only valid debit transactions
    2. split current vs historical baseline
    3. run global amount anomaly detection
    4. run category amount anomaly detection
    """
    debit_txs = get_valid_debit_transactions(txs)

    current_txs, historical_txs = split_current_and_historical_transactions(
        debit_txs,
        start_date=start_date,
        end_date=end_date,
    )

    global_anomalies = detect_global_amount_anomalies(
        current_txs=current_txs,
        historical_txs=historical_txs,
    )

    category_anomalies = detect_category_amount_anomalies(
        current_txs=current_txs,
        historical_txs=historical_txs,
    )

    anomalies = global_anomalies + category_anomalies

    return {
        "anomaly_count": len(anomalies),
        "anomalies": anomalies,
        "current_period_transaction_count": len(current_txs),
        "historical_baseline_transaction_count": len(historical_txs),
    }