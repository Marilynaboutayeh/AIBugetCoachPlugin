from fastapi import APIRouter
from app.schema.categorization import CategorizationRequest, CategorizationResponse
from app.services.categorizer import categorize

router = APIRouter()


@router.post("/categorize", response_model=CategorizationResponse)
def categorize_transaction(payload: CategorizationRequest):
    result = categorize(
        merchant_description=payload.merchant_description,
        mcc=payload.mcc,
        city=payload.city,
        country=payload.country,
        amount=payload.amount,
        date=payload.date,
    )

    # print("RAW CATEGORIZER RESULT:", result)

    return {
        "predicted_main_category": result.get("main_category"),
        "predicted_main_category_description": result.get("main_category_description"),
        "predicted_subcategory": result.get("subcategory"),
        "predicted_subcategory_description": result.get("subcategory_description"),
        "predicted_sub_subcategory": result.get("sub_subcategory"),
        "confidence": result.get("confidence"),
        "classification_source": result.get("classification_source"),
        "matched_by": result.get("matched_by"),
    }