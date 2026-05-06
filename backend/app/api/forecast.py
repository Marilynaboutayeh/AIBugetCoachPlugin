import joblib
import pandas as pd
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.transaction import Transaction
from app.services.forecast.recurring_detector import detect_recurring_candidates
from app.services.forecast.feature_builder import build_forecast_features

router = APIRouter(prefix="/v1", tags=["forecast"])

MODEL_PATH = "app/services/forecast/subscription_model.pkl"
model = joblib.load(MODEL_PATH)


@router.get("/forecast/recurring-candidates")
def get_recurring_candidates(user_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    txs: List[Transaction] = (
        db.query(Transaction)
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.timestamp.asc())
        .all()
    )

    candidates = detect_recurring_candidates(txs)

    public_candidates = []

    for candidate in candidates:
        features = build_forecast_features(candidate["transactions"])
        features_df = pd.DataFrame([features])
    
        prediction = model.predict(features_df)[0]
        confidence = model.predict_proba(features_df)[0][1]

        public_candidates.append(
            {
                "merchant": candidate["merchant"],
                "frequency": candidate["frequency"],
                "matched_transactions": candidate["matched_transactions"],
                "average_amount": candidate["average_amount"],
                "last_transaction_date": candidate["last_transaction_date"],
                "features": features,
                "ml_prediction_is_recurring": int(prediction),
                "ml_confidence": round(float(confidence), 4),
            }
        )

    return {
        "user_id": user_id,
        "recurring_candidates": public_candidates,
    }