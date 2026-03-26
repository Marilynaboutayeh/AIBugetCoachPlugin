import pandas as pd

from app.services.categorization.ml_fallback.config import (
    TRAINING_DATA_FILE,
    ML_CONFIDENCE_THRESHOLD,
)
from app.services.categorization.ml_fallback.predictor import MLFallbackPredictor


OUTPUT_FILE = TRAINING_DATA_FILE.parent / "categorized_output_with_ml_fallback.csv"


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in [
        "merchant_description",
        "merchant_token",
        "predicted_subcategory",
        "city",
        "country",
    ]:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)
        else:
            df[col] = ""

    if "amount" in df.columns:
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    else:
        df["amount"] = 0.0

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df["transaction_month"] = df["date"].dt.month.fillna(0).astype(int).astype(str)
        df["transaction_day_of_week"] = df["date"].dt.dayofweek.fillna(0).astype(int).astype(str)
    else:
        df["transaction_month"] = "0"
        df["transaction_day_of_week"] = "0"

    return df


def is_missing_main_category(value) -> bool:
    if pd.isna(value):
        return True

    value_str = str(value).strip().lower()
    return value_str == "" or value_str == "nan"


def run_batch_prediction():
    df = pd.read_csv(TRAINING_DATA_FILE)
    df = prepare_dataframe(df)

    if "predicted_main_category" not in df.columns:
        raise ValueError("Column 'predicted_main_category' not found in CSV.")

    predictor = MLFallbackPredictor()

    missing_mask = df["predicted_main_category"].apply(is_missing_main_category)
    missing_rows = df[missing_mask].copy()

    print(f"Total rows: {len(df)}")
    print(f"Rows without main category: {len(missing_rows)}")

    if missing_rows.empty:
        print("No rows need ML fallback prediction.")
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Saved file without changes to: {OUTPUT_FILE}")
        return

    predicted_categories = []
    confidences = []
    accepted_flags = []
    sources = []

    for _, row in missing_rows.iterrows():
        result = predictor.predict(
            merchant_description=row.get("merchant_description", ""),
            merchant_token=row.get("merchant_token", ""),
            predicted_subcategory=row.get("predicted_subcategory", ""),
            city=row.get("city", ""),
            country=row.get("country", ""),
            amount=row.get("amount", 0.0),
            transaction_month=row.get("transaction_month", "0"),
            transaction_day_of_week=row.get("transaction_day_of_week", "0"),
        )

        predicted_categories.append(result["predicted_main_category"])
        confidences.append(result["confidence"])
        accepted_flags.append(result["accepted_prediction"])
        sources.append(result["classification_source"])

    missing_index = df.index[missing_mask]

    df["ml_predicted_main_category"] = df.get(
        "ml_predicted_main_category",
        pd.Series(index=df.index, dtype="object"),
    )
    df["ml_confidence"] = df.get(
        "ml_confidence",
        pd.Series(index=df.index, dtype="float64"),
    )
    df["ml_accepted_prediction"] = df.get(
        "ml_accepted_prediction",
        pd.Series(index=df.index, dtype="object"),
    )
    df["ml_classification_source"] = df.get(
        "ml_classification_source",
        pd.Series(index=df.index, dtype="object"),
    )

    df.loc[missing_index, "ml_predicted_main_category"] = pd.Series(
        predicted_categories, index=missing_index, dtype="object"
    )
    df.loc[missing_index, "ml_confidence"] = pd.Series(
        confidences, index=missing_index, dtype="float64"
    )
    df.loc[missing_index, "ml_accepted_prediction"] = pd.Series(
        accepted_flags, index=missing_index, dtype="object"
    )
    df.loc[missing_index, "ml_classification_source"] = pd.Series(
        sources, index=missing_index, dtype="object"
    )

    accepted_mask = missing_mask & df["ml_accepted_prediction"].fillna(False).astype(bool)

    df.loc[accepted_mask, "predicted_main_category"] = df.loc[
        accepted_mask, "ml_predicted_main_category"
    ]
    df.loc[accepted_mask, "classification_source"] = "ml_fallback"

    print(f"Accepted ML predictions (threshold >= {ML_CONFIDENCE_THRESHOLD}): {accepted_mask.sum()}")
    print(f"Rejected / low-confidence predictions: {len(missing_rows) - accepted_mask.sum()}")

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved output file to: {OUTPUT_FILE}")


if __name__ == "__main__":
    run_batch_prediction()