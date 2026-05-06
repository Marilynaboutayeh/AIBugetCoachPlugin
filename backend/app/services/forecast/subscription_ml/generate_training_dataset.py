import argparse

from app.core.db import SessionLocal
from app.models.transaction import Transaction
from app.services.forecast.recurring_detector import detect_recurring_candidates
from app.services.forecast.subscription_ml.build_dataset import build_subscription_dataset


def generate_dataset_for_user(user_id: str, output_file: str):
    db = SessionLocal()

    try:
        txs = (
            db.query(Transaction)
            .filter(Transaction.user_id == user_id)
            .order_by(Transaction.timestamp.asc())
            .all()
        )

        recurring_candidates = detect_recurring_candidates(txs)

        output_file = build_subscription_dataset(
            recurring_candidates=recurring_candidates,
            output_file=output_file,
        )

        print(f"Dataset generated successfully: {output_file}")
        print(f"User ID: {user_id}")
        print(f"Transactions found: {len(txs)}")
        print(f"Recurring candidates found: {len(recurring_candidates)}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate subscription ML dataset from recurring candidates."
    )

    parser.add_argument(
        "--user-id",
        required=True,
        help="User ID to generate the dataset for."
    )

    parser.add_argument(
        "--output-file",
        default="subscription_training_dataset.csv",
        help="CSV file path where the dataset will be saved."
    )

    args = parser.parse_args()

    generate_dataset_for_user(
        user_id=args.user_id,
        output_file=args.output_file,
    )