from pathlib import Path
import pandas as pd

from app.services.categorization.subsubcategory_mapping.loader import (
    load_subsubcategory_to_main_category_mapping,
)


BASE_DIR = Path(__file__).resolve().parents[4]
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = "categorized_curated.csv"
OUTPUT_FILE = "categorized_curated_with_subsub_mapping.csv"

MAIN_CATEGORY_COL = "predicted_main_category"
SUB_SUBCATEGORY_COL = "predicted_sub_subcategory"
MATCHED_BY_COL = "matched_by"


def is_empty_series(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype(str).str.strip() == "")


def main():
    df = pd.read_csv(INPUT_FILE)
    subsub_to_main = load_subsubcategory_to_main_category_mapping()

    if MATCHED_BY_COL not in df.columns:
        df[MATCHED_BY_COL] = None

    main_empty_mask = is_empty_series(df[MAIN_CATEGORY_COL])
    subsub_present_mask = ~is_empty_series(df[SUB_SUBCATEGORY_COL])

    eligible_mask = main_empty_mask & subsub_present_mask

    mapped_values = (
        df.loc[eligible_mask, SUB_SUBCATEGORY_COL]
        .astype(str)
        .str.strip()
        .map(subsub_to_main)
    )

    fill_mask = eligible_mask & mapped_values.notna()

    df.loc[fill_mask, MAIN_CATEGORY_COL] = mapped_values[fill_mask]
    df.loc[fill_mask, MATCHED_BY_COL] = "sub_subcategory_mapping"

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Input rows: {len(df)}")
    print(f"Eligible rows: {eligible_mask.sum()}")
    print(f"Rows filled: {fill_mask.sum()}")
    print(f"Saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()