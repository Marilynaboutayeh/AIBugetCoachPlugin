import pandas as pd
from app.services.categorization.rule_engine import categorize_by_rules


INPUT_FILE = "./data/without_category_name.csv"
OUTPUT_FILE = "categorized_output.csv"


def main():
    df = pd.read_csv(INPUT_FILE, sep=";")

    results = []

    for _, row in df.iterrows():
        result = categorize_by_rules(
            mcc=row.get("mcc"),
            merchant_description=row.get("merchant_description"),
            city=row.get("city"),
            country=row.get("country"),
        )

        results.append({
            "merchant_description": row.get("merchant_description"),
            "mcc": row.get("mcc"),
            "city": row.get("city"),
            "country": row.get("country"),
            # "original_category_name": row.get("category_name"),
            "predicted_main_category": result.main_category,
            "predicted_main_category_description": result.main_category_description,
            "predicted_subcategory": result.subcategory,
            "predicted_subcategory_description": result.subcategory_description,
            "predicted_sub_subcategory": result.sub_subcategory,
            "confidence": result.confidence,
            "classification_source": result.classification_source,
            "matched_by": result.matched_by,
        })

    output_df = pd.DataFrame(results)
    output_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Done. Saved results to {OUTPUT_FILE}")
    print(output_df.head(10).to_string(index=False))

    unresolved = output_df["predicted_main_category"].isna().sum()
    total = len(output_df)
    print(f"\nResolved: {total - unresolved}/{total}")
    print(f"Unresolved: {unresolved}/{total}")


if __name__ == "__main__":
    main()