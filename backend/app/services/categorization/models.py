from pydantic import BaseModel
from typing import Optional


class CategorizationResult(BaseModel):
    main_category: Optional[str] = None
    main_category_description: Optional[str] = None
    subcategory: Optional[str] = None
    subcategory_description: Optional[str] = None
    sub_subcategory: Optional[str] = None
    confidence: float = 0.0
    classification_source: str = "rule_based"
    matched_by: Optional[str] = None