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

        if int(prediction) == 1:
            if confidence >= 0.90:
                confidence_level = "very_high"
                ai_message = (
                    f"AI forecast: {candidate['merchant']} is very likely to be a recurring payment. "
                    f"This prediction is based on a repeated transaction pattern with very high AI confidence."
                )
            elif confidence >= 0.75:
                confidence_level = "high"
                ai_message = (
                    f"AI forecast: {candidate['merchant']} is likely to be a recurring payment. "
                    f"This prediction is based on similar timing and amount patterns."
                )
            else:
                confidence_level = "medium"
                ai_message = (
                    f"AI forecast: {candidate['merchant']} may be a recurring payment, "
                    f"but the confidence is not high enough to fully rely on it."
                )
        else:
            confidence_level = "low"
            ai_message = (
                f"AI forecast: {candidate['merchant']} was detected as a repeated transaction pattern, "
                f"but the ML model does not classify it as a recurring payment. "
                f"It should be reviewed manually."
            )

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
                "confidence_level": confidence_level,
                "ai_message": ai_message,
            }
        )

    return {
        "user_id": user_id,
        "recurring_candidates": public_candidates,
    }