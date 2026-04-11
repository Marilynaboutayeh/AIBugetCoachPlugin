from app.services.categorization.models import CategorizationResult
from app.services.categorization.taxonomy_loader import (
    load_main_category_rules,
    load_subcategory_rules,
    load_sub_subcategory_rules,
    normalize_mcc,
)

MAIN_CATEGORY_RULES = load_main_category_rules()
SUBCATEGORY_RULES = load_subcategory_rules()
SUB_SUBCATEGORY_RULES = load_sub_subcategory_rules()


def find_subcategory_row(mcc: str):
    if not mcc:
        return None

    mcc_int = int(mcc)

    for row in SUBCATEGORY_RULES:
        if int(row["mcc_start"]) <= mcc_int <= int(row["mcc_end"]):
            return row

    return None


def find_sub_subcategory(mcc: str):
    if not mcc:
        return None

    for row in SUB_SUBCATEGORY_RULES:
        if row["mcc"] == mcc:
            return row["sub_subcategory"]

    return None


def find_main_category_row(mcc: str):
    if not mcc:
        return None

    mcc_int = int(mcc)

    for row in MAIN_CATEGORY_RULES:
        if int(row["mcc_start"]) <= mcc_int <= int(row["mcc_end"]):
            return row

    return None


def categorize_by_rules(mcc, merchant_description=None, city=None, country=None):
    normalized_mcc = normalize_mcc(mcc)

    subcategory_row = find_subcategory_row(normalized_mcc)
    main_category_row = find_main_category_row(normalized_mcc)
    sub_subcategory = find_sub_subcategory(normalized_mcc)

    subcategory = subcategory_row["subcategory"] if subcategory_row else None
    subcategory_description = subcategory_row["description"] if subcategory_row else None

    main_category = main_category_row["main_category"] if main_category_row else None
    main_category_description = main_category_row["description"] if main_category_row else None

    if main_category:
        return CategorizationResult(
            main_category=main_category,
            main_category_description=main_category_description,
            subcategory=subcategory,
            subcategory_description=subcategory_description,
            sub_subcategory=sub_subcategory,
            confidence=0.95,
            classification_source="rule_based",
            matched_by="mcc_rule",
        )

    return CategorizationResult(
        main_category=None,
        main_category_description=None,
        subcategory=subcategory,
        subcategory_description=subcategory_description,
        sub_subcategory=sub_subcategory,
        confidence=0.0,
        classification_source="rule_based",
        matched_by=None,
    )