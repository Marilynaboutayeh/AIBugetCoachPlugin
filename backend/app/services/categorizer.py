# from app.services.categorization.rule_engine import categorize_by_rules


# class CategorizerService:
#     def categorize_transaction(
#         self,
#         mcc,
#         merchant_description=None,
#         city=None,
#         country=None,
#         amount=None,
#         date=None,
#     ):
#         rule_result = categorize_by_rules(
#             mcc=mcc,
#             merchant_description=merchant_description,
#             city=city,
#             country=country,
#         )

#         # later:
#         # if rule_result.main_category is None:
#         #     return ml_fallback(
#         #         mcc=mcc,
#         #         merchant_description=merchant_description,
#         #         city=city,
#         #         country=country,
#         #         amount=amount,
#         #         date=date,
#         #     )

#         return {
#             "predicted_main_category": rule_result.main_category,
#             "predicted_main_category_description": rule_result.main_category_description,
#             "predicted_subcategory": rule_result.subcategory,
#             "predicted_subcategory_description": rule_result.subcategory_description,
#             "predicted_sub_subcategory": rule_result.sub_subcategory,
#             "confidence": rule_result.confidence,
#             "classification_source": rule_result.classification_source,
#             "matched_by": rule_result.matched_by,
#         }


# def categorize(
#     merchant_description: str,
#     mcc: str,
#     city: str,
#     country: str,
#     amount=None,
#     date=None,
# ):
#     service = CategorizerService()
#     return service.categorize_transaction(
#         mcc=mcc,
#         merchant_description=merchant_description,
#         city=city,
#         country=country,
#         amount=amount,
#         date=date,
#     )


from datetime import datetime

from app.services.categorization.rule_engine import categorize_by_rules
from app.services.categorization.ml_fallback.predictor import MLFallbackPredictor


ml_fallback_predictor = MLFallbackPredictor()


class CategorizerService:
    def _extract_date_features(self, date_value):
        if not date_value:
            return "0", "0"

        try:
            parsed_date = datetime.fromisoformat(str(date_value))
            return str(parsed_date.month), str(parsed_date.weekday())
        except Exception:
            return "0", "0"

    def categorize_transaction(
        self,
        mcc,
        merchant_description=None,
        merchant_token=None,
        city=None,
        country=None,
        amount=None,
        date=None,
    ):
        rule_result = categorize_by_rules(
            mcc=mcc,
            merchant_description=merchant_description,
            city=city,
            country=country,
        )

        # 1. Rule-based first
        if rule_result.main_category:
            return {
                "predicted_main_category": rule_result.main_category,
                "predicted_main_category_description": rule_result.main_category_description,
                "predicted_subcategory": rule_result.subcategory,
                "predicted_subcategory_description": rule_result.subcategory_description,
                "predicted_sub_subcategory": rule_result.sub_subcategory,
                "confidence": rule_result.confidence,
                "classification_source": rule_result.classification_source,
                "matched_by": rule_result.matched_by,
            }

        # 2. ML fallback if no main category from rules
        transaction_month, transaction_day_of_week = self._extract_date_features(date)

        ml_result = ml_fallback_predictor.predict(
            merchant_description=merchant_description or "",
            merchant_token=merchant_token or "",
            predicted_subcategory=rule_result.subcategory or "",
            # predicted_sub_subcategory=rule_result.sub_subcategory or "",
            city=city or "",
            country=country or "",
            amount=amount if amount is not None else 0.0,
            transaction_month=transaction_month,
            transaction_day_of_week=transaction_day_of_week,
        )

        if ml_result["accepted_prediction"]:
            return {
                "predicted_main_category": ml_result["predicted_main_category"],
                "predicted_main_category_description": None,
                "predicted_subcategory": rule_result.subcategory,
                "predicted_subcategory_description": rule_result.subcategory_description,
                "predicted_sub_subcategory": rule_result.sub_subcategory,
                "confidence": ml_result["confidence"],
                "classification_source": "ml_fallback",
                "matched_by": "ml_fallback",
            }

        # 3. If ML is also not confident, return unresolved
        return {
            "predicted_main_category": None,
            "predicted_main_category_description": None,
            "predicted_subcategory": rule_result.subcategory,
            "predicted_subcategory_description": rule_result.subcategory_description,
            "predicted_sub_subcategory": rule_result.sub_subcategory,
            "confidence": ml_result["confidence"],
            "classification_source": "ml_fallback",
            "matched_by": "low_confidence_ml_fallback",
        }


def categorize(
    merchant_description: str,
    mcc: str,
    city: str,
    country: str,
    amount=None,
    date=None,
    merchant_token=None,
):
    service = CategorizerService()
    return service.categorize_transaction(
        mcc=mcc,
        merchant_description=merchant_description,
        merchant_token=merchant_token,
        city=city,
        country=country,
        amount=amount,
        date=date,
    )


if __name__ == "__main__":
    result = categorize(
        merchant_description="zara",
        merchant_token="zara",
        mcc="5691",
        city="beirut",
        country="lebanon",
        amount=120.0,
        date="2026-03-25",
    )
    print(result)