import re
from typing import List, Optional

# Generic noisy words often found in bank transaction descriptions
NOISE_WORDS = {
    "payment", "purchase", "card", "pos", "debit", "credit", "online",
    "transaction", "intl", "international", "ref", "reference",
    "visa", "mastercard", "bank", "transfer", "trf", "txn",
    "wdl", "atm", "withdrawal", "deposit", "mobile", "app",
    "www", "com", "lb", "lbn", "lebanon", "beirut", "sal", "sarl",
    "co", "company", "store", "shop",
    "help", "order", "domain", "appl", "ppmt"
}

def normalize_text(text: Optional[str]) -> str:
    """
    Lowercase text, remove punctuation/special characters,
    and collapse multiple spaces.
    """
    if not text:
        return ""

    text = text.lower()

    # Replace non-alphanumeric characters with spaces
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def remove_noise_tokens(tokens: List[str]) -> List[str]:
    """
    Remove numbers, noisy banking words, short junk tokens,
    and id-like alphanumeric tokens.
    """
    cleaned = []

    for token in tokens:
        if not token:
            continue

        # Remove pure digits
        if token.isdigit():
            continue

        # Remove tokens containing any digit
        if any(char.isdigit() for char in token):
            continue

        # Remove very short tokens
        if len(token) <= 1:
            continue

        # Remove 2-letter country-like suffixes
        if len(token) == 2:
            continue

        # Remove noise words
        if token in NOISE_WORDS:
            continue

        cleaned.append(token)

    return cleaned


def build_merchant_token(merchant_description: Optional[str]) -> str:
    """
    Convert raw merchant description into a cleaned merchant token string
    to be used later as an ML feature.
    """
    text = normalize_text(merchant_description)
    if not text:
        return ""

    tokens = text.split()
    tokens = remove_noise_tokens(tokens)

    # Remove duplicates while preserving order
    seen = set()
    final_tokens = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            final_tokens.append(token)

    return " ".join(final_tokens)