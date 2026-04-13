from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from app.services.categorization.ml_fallback.config import (
    TRAINING_DATA_FILE,
    TARGET_COLUMN,
    TEXT_COLUMNS,
    CATEGORICAL_COLUMNS,
    NUMERIC_COLUMNS,
    DATE_COLUMNS,
    RANDOM_STATE,
    TEST_SIZE,
)

# Minimum number of rows required for a (main_category, subcategory) pair
# to be included in the stratified train/test split.
# Pairs below this threshold are added to train only.
MIN_PAIR_COUNT = 3

# Column used as helper/context feature and as fairness key in the split
SUBCATEGORY_COLUMN = "predicted_subcategory"


def load_training_data() -> pd.DataFrame:
    """
    Load the categorized CSV used for ML fallback training.
    """
    return pd.read_csv(TRAINING_DATA_FILE)


def clean_text(value) -> str:
    """
    Convert a value to a clean lowercase string.
    """
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def prepare_training_dataframe() -> pd.DataFrame:
    """
    Load and clean the dataset for ML training.
    """
    df = load_training_data().copy()

    # Keep only rows that have a valid target label
    df = df[df[TARGET_COLUMN].notna()].copy()
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(str).str.strip()
    df = df[
        (df[TARGET_COLUMN] != "")
        & (df[TARGET_COLUMN].str.lower() != "nan")
    ].copy()

    # Clean text columns
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)
        else:
            df[col] = ""

    # Clean categorical columns
    for col in CATEGORICAL_COLUMNS:
        if col in df.columns:
            df[col] = df[col].apply(clean_text)
        else:
            df[col] = ""

    # Clean numeric columns
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        else:
            df[col] = 0.0

    # Clean date columns
    for col in DATE_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
        else:
            df[col] = pd.NaT

    # Clean target
    df[TARGET_COLUMN] = df[TARGET_COLUMN].apply(clean_text)

    # Make sure subcategory exists and is cleaned
    if SUBCATEGORY_COLUMN not in df.columns:
        df[SUBCATEGORY_COLUMN] = ""
    df[SUBCATEGORY_COLUMN] = df[SUBCATEGORY_COLUMN].apply(clean_text)

    # Create combined text field
    merchant_description = (
        df["merchant_description"] if "merchant_description" in df.columns else ""
    )
    merchant_token = (
        df["merchant_token"] if "merchant_token" in df.columns else ""
    )

    df["combined_text"] = (
        merchant_description.fillna("").astype(str)
        + " "
        + merchant_token.fillna("").astype(str)
    ).str.strip()

    # Date-derived features
    if "date" in df.columns:
        df["transaction_month"] = (
            df["date"].dt.month.fillna(0).astype(int).astype(str)
        )
        df["transaction_day_of_week"] = (
            df["date"].dt.dayofweek.fillna(0).astype(int).astype(str)
        )
    else:
        df["transaction_month"] = "0"
        df["transaction_day_of_week"] = "0"

    # Create fairness key: main_category + subcategory
    df["pair_label"] = (
        df[TARGET_COLUMN].fillna("").astype(str)
        + "||"
        + df[SUBCATEGORY_COLUMN].fillna("").astype(str)
    )

    return df


def get_feature_columns() -> list[str]:
    """
    Return the columns used as model input features.
    """
    return [
        "combined_text",
        "predicted_subcategory",
        # "predicted_sub_subcategory",
        "city",
        "country",
        "amount",
        "transaction_month",
        "transaction_day_of_week",
    ]


def build_training_matrices():
    """
    Build X and y for training.
    """
    df = prepare_training_dataframe()
    feature_columns = get_feature_columns()

    X = df[feature_columns].copy()
    y = df[TARGET_COLUMN].copy()

    return X, y, df


def split_training_data():
    """
    Split the dataset into train and test sets fairly using the
    (main_category, predicted_subcategory) combination.

    Logic:
    - keep all rows with valid target labels
    - create pair_label = main_category || predicted_subcategory
    - pairs with count >= MIN_PAIR_COUNT go to stratified split
    - rare pairs (< MIN_PAIR_COUNT) are added to train only
    """
    X, y, df = build_training_matrices()

    pair_counts = df["pair_label"].value_counts()

    common_pairs = pair_counts[pair_counts >= MIN_PAIR_COUNT].index
    rare_pairs = pair_counts[pair_counts < MIN_PAIR_COUNT].index

    df_common = df[df["pair_label"].isin(common_pairs)].copy()
    df_rare = df[df["pair_label"].isin(rare_pairs)].copy()

    if df_common.empty:
        raise ValueError(
            "No common (main_category, predicted_subcategory) pairs found. "
            "Lower MIN_PAIR_COUNT or inspect the training data."
        )

    # Need at least 2 different pair classes for stratified split
    if df_common["pair_label"].nunique() < 2:
        raise ValueError(
            "Not enough distinct common pair_label classes for stratified split."
        )

    train_common_idx, test_idx = train_test_split(
        df_common.index,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=df_common["pair_label"],
    )

    # Rare pairs go to train only
    train_idx = pd.Index(train_common_idx).append(df_rare.index)

    X_train = X.loc[train_idx].copy()
    X_test = X.loc[test_idx].copy()
    y_train = y.loc[train_idx].copy()
    y_test = y.loc[test_idx].copy()

    return X_train, X_test, y_train, y_test, df


def export_train_test_data():
    """
    Export X_train and X_test with target for inspection.
    """
    X_train, X_test, y_train, y_test, _ = split_training_data()

    output_dir = Path("debug_ml_data")
    output_dir.mkdir(exist_ok=True)

    train_df = X_train.copy()
    train_df["target_main_category"] = y_train.values

    test_df = X_test.copy()
    test_df["target_main_category"] = y_test.values

    train_df.to_csv(output_dir / "train_data.csv", index=False)
    test_df.to_csv(output_dir / "test_data.csv", index=False)

    print("Train/Test CSV files exported successfully.")
    print(f"Train file: {output_dir / 'train_data.csv'}")
    print(f"Test file: {output_dir / 'test_data.csv'}")


def inspect_pair_distribution():
    """
    Inspect the distribution of (main_category, predicted_subcategory) pairs
    in the full dataset, train set, and test set.
    """
    X_train, X_test, y_train, y_test, df = split_training_data()

    train_idx = X_train.index
    test_idx = X_test.index

    train_df = df.loc[train_idx].copy()
    test_df = df.loc[test_idx].copy()

    print("Full dataset size:", len(df))
    print("Train size:", len(train_df))
    print("Test size:", len(test_df))
    print()

    print("Unique pair_label count in full data:", df["pair_label"].nunique())
    print("Unique pair_label count in train:", train_df["pair_label"].nunique())
    print("Unique pair_label count in test:", test_df["pair_label"].nunique())
    print()

    print("Top full pair_label counts:")
    print(df["pair_label"].value_counts().head(20))
    print()

    print("Top train pair_label counts:")
    print(train_df["pair_label"].value_counts().head(20))
    print()

    print("Top test pair_label counts:")
    print(test_df["pair_label"].value_counts().head(20))
    print()

    rare_pair_counts = df["pair_label"].value_counts()
    rare_pairs = rare_pair_counts[rare_pair_counts < MIN_PAIR_COUNT]

    print(f"Number of rare pairs (< {MIN_PAIR_COUNT} rows):", len(rare_pairs))
    if not rare_pairs.empty:
        print("Sample rare pairs:")
        print(rare_pairs.head(20))


def inspect_train_test_overlap():
    """
    Check overlap of merchant patterns between train and test.

    Note:
    With the new fair stratified split, overlap in combined_text may happen.
    This function is now only informational and no longer a strict leakage test.
    """
    X_train, X_test, _, _, df = split_training_data()

    train_idx = X_train.index
    test_idx = X_test.index

    train_texts = set(df.loc[train_idx, "combined_text"])
    test_texts = set(df.loc[test_idx, "combined_text"])
    text_overlap = train_texts.intersection(test_texts)

    print("Unique train combined_text:", len(train_texts))
    print("Unique test combined_text:", len(test_texts))
    print("Overlapping combined_text:", len(text_overlap))

    if text_overlap:
        print("\nSample overlapping combined_text values:")
        for value in list(text_overlap)[:10]:
            print(value)


if __name__ == "__main__":
    X_train, X_test, y_train, y_test, df = split_training_data()

    print("Dataset loaded successfully.")
    print("Full dataset shape:", df.shape)
    print("Number of target classes:", df[TARGET_COLUMN].nunique())
    print("Number of pair_label classes:", df["pair_label"].nunique())
    print("Feature columns:", X_train.columns.tolist())
    print("X_train shape:", X_train.shape)
    print("X_test shape:", X_test.shape)
    print("y_train shape:", y_train.shape)
    print("y_test shape:", y_test.shape)
    print()
    print("Sample X_train rows:")
    print(X_train.head())
    print()
    print("Sample y_train rows:")
    print(y_train.head())