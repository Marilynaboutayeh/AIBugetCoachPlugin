from typing import Optional

def categorize(merchant: Optional[str], description: Optional[str]) -> str:
    """
    Rules-based categorizer.
    Uses merchant/description text to assign a category.
    """
    text = f"{merchant or ''} {description or ''}".upper()

    rules = [
    (["NETFLIX", "SUBSCRIPTION", "SPOTIFY", "ANGHAMI", "OSN", "SHAHID", "CHATGPT", "OPENAI"], "Subscriptions"),
    (["UBER", "BOLT", "TAXI"], "Travel"),
    (["CARREFOUR", "SPINNEYS", "TOTERS", "NOKNOK", "GROCERY", "SUPERMARKET"], "Groceries"),
    (["ZARA", "AZADEA", "H&M", "BERSHKA", "STRADIVARIUS", "NIKE", "ADIDAS"], "Shopping Online"),
    (["MCDONALD", "BURGER KING", "KFC", "PIZZA", "RESTAURANT", "CAFE", "STARBUCKS"], "Food and Drink"),
    (["PHARM", "HOSPITAL", "CLINIC"], "Health"),
    (["ELECTRIC", "WATER", "INTERNET", "MOBILE", "OGERO", "TOUCH", "ALFA", "EDL"], "Bills"),
    (["OMT", "WHISH", "WESTERN UNION"], "Transfers"),
]

    for keywords, category in rules:
        if any(k in text for k in keywords):
            return category

    return "Other"

