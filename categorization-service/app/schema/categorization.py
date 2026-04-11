from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class CategorizationRequest(BaseModel):
    merchant_description: Optional[str] = None
    mcc: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[datetime] = None


class CategorizationResponse(BaseModel):
    predicted_main_category: Optional[str] = None
    predicted_main_category_description: Optional[str] = None
    predicted_subcategory: Optional[str] = None
    predicted_subcategory_description: Optional[str] = None
    predicted_sub_subcategory: Optional[str] = None
    confidence: Optional[float] = None
    classification_source: Optional[str] = None
    matched_by: Optional[str] = None