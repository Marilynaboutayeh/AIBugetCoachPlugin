import pandas as pd
from pathlib import Path

from app.services.categorizer import categorize
from app.services.categorization.merchant_tokenizer import build_merchant_token


INPUT_FILE = Path("./data/without_category_name.csv")
OUTPUT_FILE = Path("./categorized_output.csv")


def main():
    if not INPUT_FILE.exists():
        print(f"Input file not found: {INPUT_FILE}")
        return

    df = pd.read_csv(INPUT_FILE, sep=";")

    results = []

    for _, row in df.iterrows():
        merchant_description = row.get("merchant_description")

        result = categorize(
            merchant_description=merchant_description,
            mcc=row.get("mcc"),
            city=row.get("city"),
            country=row.get("country"),
        )

        merchant_token = build_merchant_token(merchant_description)

        results.append({
            "merchant_description": merchant_description,
            "merchant_token": merchant_token,
            "mcc": row.get("mcc"),
            "city": row.get("city"),
            "country": row.get("country"),
            # "original_category_name": row.get("category_name"),

            "predicted_main_category": result.get("predicted_main_category"),
            "predicted_main_category_description": result.get("predicted_main_category_description"),
            "predicted_subcategory": result.get("predicted_subcategory"),
            "predicted_subcategory_description": result.get("predicted_subcategory_description"),
            "predicted_sub_subcategory": result.get("predicted_sub_subcategory"),
            "confidence": result.get("confidence"),
            "classification_source": result.get("classification_source"),
            "matched_by": result.get("matched_by"),
        })

    output_df = pd.DataFrame(results)
    output_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Done. Saved results to {OUTPUT_FILE.resolve()}")
    print(output_df.head(10).to_string(index=False))

    unresolved = output_df["predicted_main_category"].isna().sum()
    total = len(output_df)
    print(f"\nResolved: {total - unresolved}/{total}")
    print(f"Unresolved: {unresolved}/{total}")


if __name__ == "__main__":
    main()