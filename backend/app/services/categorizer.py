from datetime import datetime

from app.services.categorization.rule_engine import categorize_by_rules
from app.services.categorization.ml_fallback.predictor import MLFallbackPredictor
from app.services.categorization.subsubcategory_mapping.mapper import (
    map_main_category_if_empty,
)
from app.services.categorization.taxonomy_loader import load_main_category_rules
from app.services.categorization.merchant_tokenizer import build_merchant_token


ml_fallback_predictor = MLFallbackPredictor()


def _build_main_category_description_map() -> dict[str, str]:
    description_map = {}

    try:
        rows = load_main_category_rules()
        for row in rows:
            main_category = str(row.get("main_category", "")).strip()
            description = str(row.get("description", "")).strip()

            if main_category and main_category.lower() != "nan":
                description_map[main_category] = (
                    description if description and description.lower() != "nan" else None
                )
    except Exception:
        pass

    return description_map


MAIN_CATEGORY_DESCRIPTION_MAP = _build_main_category_description_map()


class CategorizerService:
    def _extract_date_features(self, date_value):
        if not date_value:
            return "0", "0"

        try:
            parsed_date = datetime.fromisoformat(str(date_value))
            return str(parsed_date.month), str(parsed_date.weekday())
        except Exception:
            return "0", "0"

    def _get_main_category_description(self, main_category):
        if not main_category:
            return None
        return MAIN_CATEGORY_DESCRIPTION_MAP.get(str(main_category).strip())

    def categorize_transaction(
        self,
        mcc,
        merchant_description=None,
        city=None,
        country=None,
        amount=None,
        date=None,
    ):
        merchant_description = merchant_description or ""
        merchant_token = build_merchant_token(merchant_description)

        rule_result = categorize_by_rules(
            mcc=mcc,
            merchant_description=merchant_description,
            city=city,
            country=country,
        )

        # 1) RULE-BASED
        if rule_result.main_category:
            return {
                "main_category": rule_result.main_category,
                "main_category_description": rule_result.main_category_description,
                "subcategory": rule_result.subcategory,
                "subcategory_description": rule_result.subcategory_description,
                "sub_subcategory": rule_result.sub_subcategory,
                "confidence": rule_result.confidence,
                "classification_source": "rule_based",
                "matched_by": rule_result.matched_by or "mcc_rule",
            }

        # 2) SUB-SUBCATEGORY MAPPING
        mapped_main_category = map_main_category_if_empty(
            predicted_main_category=rule_result.main_category,
            predicted_sub_subcategory=rule_result.sub_subcategory,
        )

        if mapped_main_category:
            return {
                "main_category": mapped_main_category,
                "main_category_description": self._get_main_category_description(mapped_main_category),
                "subcategory": rule_result.subcategory,
                "subcategory_description": rule_result.subcategory_description,
                "sub_subcategory": rule_result.sub_subcategory,
                "confidence": 0.95,
                "classification_source": "subsubcategory_mapping",
                "matched_by": "sub_subcategory_mapping",
            }

        # 3) ML FALLBACK
        transaction_month, transaction_day_of_week = self._extract_date_features(date)

        ml_result = ml_fallback_predictor.predict(
            merchant_description=merchant_description,
            merchant_token=merchant_token,
            predicted_subcategory=rule_result.subcategory or "",
            city=city or "",
            country=country or "",
            amount=amount if amount is not None else 0.0,
            transaction_month=transaction_month,
            transaction_day_of_week=transaction_day_of_week,
        )

        if ml_result.get("accepted_prediction"):
            predicted_main_category = ml_result.get("predicted_main_category")

            return {
                "main_category": predicted_main_category,
                "main_category_description": self._get_main_category_description(predicted_main_category),
                "subcategory": rule_result.subcategory,
                "subcategory_description": rule_result.subcategory_description,
                "sub_subcategory": rule_result.sub_subcategory,
                "confidence": ml_result.get("confidence"),
                "classification_source": "ml_fallback",
                "matched_by": "ml_fallback",
            }

        # 4) UNCERTAIN
        return {
            "main_category": None,
            "main_category_description": None,
            "subcategory": rule_result.subcategory,
            "subcategory_description": rule_result.subcategory_description,
            "sub_subcategory": rule_result.sub_subcategory,
            "confidence": ml_result.get("confidence"),
            "classification_source": "uncertain",
            "matched_by": "low_confidence_ml_fallback",
        }


def categorize(
    merchant_description: str,
    mcc: str,
    city: str,
    country: str,
    amount=None,
    date=None,
):
    service = CategorizerService()
    return service.categorize_transaction(
        mcc=mcc,
        merchant_description=merchant_description,
        city=city,
        country=country,
        amount=amount,
        date=date,
    )


if __name__ == "__main__":
    result = categorize(
        merchant_description="spotify",
        mcc="5815",
        city="beirut",
        country="lebanon",
        amount=20.0,
        date="2026-03-25",
    )
    print(result)