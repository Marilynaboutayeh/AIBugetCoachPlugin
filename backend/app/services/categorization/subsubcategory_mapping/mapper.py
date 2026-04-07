from app.services.categorization.subsubcategory_mapping.loader import (
    load_subsubcategory_to_main_category_mapping,
)


SUBSUB_TO_MAIN = load_subsubcategory_to_main_category_mapping()


def is_empty(value) -> bool:
    if value is None:
        return True
    value_str = str(value).strip()
    return value_str == "" or value_str.lower() == "nan"


def map_main_category_if_empty(
    predicted_main_category,
    predicted_sub_subcategory,
):
    """
    Fill main category only if it is empty.
    Never overwrite an existing main category.
    """
    if not is_empty(predicted_main_category):
        return predicted_main_category

    if is_empty(predicted_sub_subcategory):
        return predicted_main_category

    mapped_main = SUBSUB_TO_MAIN.get(str(predicted_sub_subcategory).strip())

    if mapped_main:
        return mapped_main

    return predicted_main_category