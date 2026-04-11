import httpx

CATEGORIZATION_SERVICE_URL = "http://127.0.0.1:8001/internal/categorize"


def categorize_via_service(
    merchant_description: str,
    mcc: str,
    city: str,
    country: str,
    amount=None,
    date=None,
):
    payload = {
        "merchant_description": merchant_description,
        "mcc": mcc,
        "city": city,
        "country": country,
        "amount": amount,
        "date": date.isoformat() if date else None,
    }

    response = httpx.post(CATEGORIZATION_SERVICE_URL, json=payload, timeout=10.0)
    response.raise_for_status()
    return response.json()