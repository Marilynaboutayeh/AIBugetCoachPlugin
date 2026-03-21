from app.services.categorization.rule_engine import categorize_by_rules

examples = [
    {"mcc": "5411", "merchant_description": "Carrefour"},
    {"mcc": "5812", "merchant_description": "McDonalds"},
    {"mcc": "4900", "merchant_description": "Electricite du Liban"},
    {"mcc": "0742", "merchant_description": "Veterinarni Klinika"},
    {"mcc": "742", "merchant_description": "Veterinarni Klinika"},
]

for example in examples:
    result = categorize_by_rules(
        mcc=example["mcc"],
        merchant_description=example["merchant_description"],
    )
    print("INPUT:", example)
    print("OUTPUT:", result.model_dump())
    print("-" * 50)