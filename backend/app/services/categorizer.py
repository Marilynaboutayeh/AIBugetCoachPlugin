# from typing import Optional

# def categorize(merchant: Optional[str], description: Optional[str]) -> str:
#     """
#     Rules-based categorizer.
#     Uses merchant/description text to assign a category.
#     """
#     text = f"{merchant or ''} {description or ''}".upper()

#     rules = [
#     (["NETFLIX", "SUBSCRIPTION", "SPOTIFY", "ANGHAMI", "OSN", "SHAHID", "CHATGPT", "OPENAI"], "Subscriptions"),
#     (["UBER", "BOLT", "TAXI"], "Travel"),
#     (["CARREFOUR", "SPINNEYS", "TOTERS", "NOKNOK", "GROCERY", "SUPERMARKET"], "Groceries"),
#     (["ZARA", "AZADEA", "H&M", "BERSHKA", "STRADIVARIUS", "NIKE", "ADIDAS"], "Shopping Online"),
#     (["MCDONALD", "BURGER KING", "KFC", "PIZZA", "RESTAURANT", "CAFE", "STARBUCKS"], "Food and Drink"),
#     (["PHARM", "HOSPITAL", "CLINIC"], "Health"),
#     (["ELECTRIC", "WATER", "INTERNET", "MOBILE", "OGERO", "TOUCH", "ALFA", "EDL"], "Bills"),
#     (["OMT", "WHISH", "WESTERN UNION"], "Transfers"),
# ]

#     for keywords, category in rules:
#         if any(k in text for k in keywords):
#             return category

#     return "Other"

from app.services.categorization.rule_engine import categorize_by_rules


class CategorizerService:
    def categorize_transaction(
        self,
        mcc,
        merchant_description=None,
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

        # later:
        # if rule_result.main_category is None:
        #     return ml_fallback(
        #         mcc=mcc,
        #         merchant_description=merchant_description,
        #         city=city,
        #         country=country,
        #         amount=amount,
        #         date=date,
        #     )

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