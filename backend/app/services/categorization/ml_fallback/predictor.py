import joblib
import pandas as pd

from app.services.categorization.ml_fallback.config import (
    MODEL_FILE,
    ML_CONFIDENCE_THRESHOLD,
)


class MLFallbackPredictor:
    def __init__(self):
        self.model = joblib.load(MODEL_FILE)

    @staticmethod
    def _clean_text(value) -> str:
        if value is None:
            return ""
        return str(value).strip().lower()

    def prepare_input(
        self,
        merchant_description: str = "",
        merchant_token: str = "",
        predicted_subcategory: str = "",
        city: str = "",
        country: str = "",
        amount: float = 0.0,
        transaction_month: str = "0",
        transaction_day_of_week: str = "0",
    ) -> pd.DataFrame:
        combined_text = (
            f"{self._clean_text(merchant_description)} "
            f"{self._clean_text(merchant_token)}"
        ).strip()

        row = {
            "combined_text": combined_text,
            "predicted_subcategory": self._clean_text(predicted_subcategory),
            "city": self._clean_text(city),
            "country": self._clean_text(country),
            "amount": float(amount) if amount is not None else 0.0,
            "transaction_month": str(transaction_month),
            "transaction_day_of_week": str(transaction_day_of_week),
        }

        return pd.DataFrame([row])

    def predict(
        self,
        merchant_description: str = "",
        merchant_token: str = "",
        predicted_subcategory: str = "",
        city: str = "",
        country: str = "",
        amount: float = 0.0,
        transaction_month: str = "0",
        transaction_day_of_week: str = "0",
    ) -> dict:
        X = self.prepare_input(
            merchant_description=merchant_description,
            merchant_token=merchant_token,
            predicted_subcategory=predicted_subcategory,
            city=city,
            country=country,
            amount=amount,
            transaction_month=transaction_month,
            transaction_day_of_week=transaction_day_of_week,
        )

        predicted_label = self.model.predict(X)[0]
        predicted_probabilities = self.model.predict_proba(X)[0]
        max_confidence = float(predicted_probabilities.max())

        return {
            "predicted_main_category": predicted_label,
            "confidence": max_confidence,
            "classification_source": "ml_fallback",
            "accepted_prediction": max_confidence >= ML_CONFIDENCE_THRESHOLD,
        }


if __name__ == "__main__":
    predictor = MLFallbackPredictor()

    result = predictor.predict(
        merchant_description="zara",
        merchant_token="zara",
        predicted_subcategory="clothing store",
        city="beirut",
        country="lebanon",
        amount=120.0,
        transaction_month="3",
        transaction_day_of_week="2",
    )

    print(result)