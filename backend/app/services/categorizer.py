from typing import Optional

def categorize(merchant: Optional[str], description: Optional[str]) -> str:
    """
    Rules-based categorizer.
    Uses merchant/description text to assign a category.
    """
    text = f"{merchant or ''} {description or ''}".upper()

    rules = [
        (["UBER", "BOLT", "TAXI"], "Transport"),
        (["NETFLIX", "SPOTIFY", "ANGHAMI", "OSN", "SHAHID","CHATGPT", "OPENAI"], "Subscriptions"),
        (["CARREFOUR", "SPINNEYS", "HAPPY", "TOTERS", "NOKNOK", "GROCER", "MARKET", "SUPERMARKET"], "Groceries"),
        (["ZARA", "H&M", "BERSHKA", "STRADIVARIUS", "NIKE", "ADIDAS"], "Shopping"),
        (["MCDONALD","BURGER KING", "KFC", "PIZZA", "RESTAURANT", "CAFE", "STARBUCKS"], "Food & Drink"),
        (["PHARM", "HOSPITAL", "CLINIC"], "Health"),
        (["ELECTRIC", "WATER", "INTERNET", "MOBILE", "OGERO"], "Bills"),
    ]

    for keywords, category in rules:
        if any(k in text for k in keywords):
            return category

    return "Other"