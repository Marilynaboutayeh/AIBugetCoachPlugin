import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


DATASET_PATH = "data/forecast_candidates_for_labeling.csv"
MODEL_OUTPUT_PATH = "app/services/forecast/subscription_model.pkl"


def train_forecast_model():
    df = pd.read_csv(DATASET_PATH)

    X = df.drop(columns=["is_recurring"])
    y = df["is_recurring"]

    categorical_features = [
        "merchant_token",
        "mcc",
        "main_category",
    ]

    numerical_features = [
        "amount_avg",
        "amount_std",
        "interval_avg_days",
        "interval_std_days",
        "occurrence_count",
    ]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_features,
            ),
            (
                "numerical",
                "passthrough",
                numerical_features,
            ),
        ]
    )

    model_pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", LogisticRegression(max_iter=1000, class_weight="balanced")),
        ]
    )

    model_pipeline.fit(X, y)

    joblib.dump(model_pipeline, MODEL_OUTPUT_PATH)

    print("Model trained successfully")
    print(f"Model saved at: {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    train_forecast_model()