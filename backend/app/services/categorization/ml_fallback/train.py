import joblib
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.services.categorization.ml_fallback.config import (
    ARTIFACTS_DIR,
    MODEL_FILE,
)
from app.services.categorization.ml_fallback.preprocessor import split_training_data


TEXT_FEATURE = "combined_text"
CATEGORICAL_FEATURES = [
    # "mcc",
    "predicted_subcategory",
    # "predicted_sub_subcategory",
    "city",
    "country",
    "transaction_month",
    "transaction_day_of_week",
]
NUMERIC_FEATURES = [
    # "amount",
]


def build_model_pipeline() -> Pipeline:
    """
    Build the preprocessing + classification pipeline.
    """
    text_transformer = TfidfVectorizer(
        ngram_range=(1, 2),
        min_df=2,
        max_features=5000,
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value=0.0)),
            ("scaler", StandardScaler()),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("text", text_transformer, TEXT_FEATURE),
            ("cat", categorical_transformer, CATEGORICAL_FEATURES),
            # ("num", numeric_transformer, NUMERIC_FEATURES),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000)),
        ]
    )

    return model


def train_and_evaluate():
    """
    Train the fallback model and evaluate it on the test set.
    """
    X_train, X_test, y_train, y_test, _ = split_training_data()

    model = build_model_pipeline()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    print("Training completed.")
    print(f"Accuracy: {accuracy:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")
    print(f"Weighted F1: {weighted_f1:.4f}")
    print()
    print("Classification report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_FILE)

    print()
    print(f"Model saved to: {MODEL_FILE}")

    return model


if __name__ == "__main__":
    train_and_evaluate()