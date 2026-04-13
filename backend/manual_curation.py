import pandas as pd

INPUT_FILE = "categorized_output.csv"
OUTPUT_FILE = "categorized_curated.csv"

SUBCATEGORY_COLUMN = "predicted_subcategory"
MAIN_CATEGORY_COLUMN = "predicted_main_category"
CURATED_FLAG_COLUMN = "manually_curated"

RANDOM_STATE = 42

# format: subcategory -> (new main category, number of rows to curate)
CURATION_PLAN = {
    "digital goods": ("shopping", 170),
    "business services": ("professional services", 75),
    "repair services": ("fuel & automotive", 70),
    "miscellaneous professional services": ("professional services", 12),
    "car rental": ("transport & taxis", 10),
    "membership organizations": ("professional services", 3),
    "social services": ("professional services", 10),
}


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def is_empty_label(value) -> bool:
    cleaned = clean_text(value)
    return cleaned in {"", "nan", "none", "null"}


def main():
    df = pd.read_csv(INPUT_FILE).copy()

    if SUBCATEGORY_COLUMN not in df.columns:
        raise ValueError(f"Missing column: {SUBCATEGORY_COLUMN}")
    if MAIN_CATEGORY_COLUMN not in df.columns:
        raise ValueError(f"Missing column: {MAIN_CATEGORY_COLUMN}")

    df[SUBCATEGORY_COLUMN] = df[SUBCATEGORY_COLUMN].apply(clean_text)
    df[MAIN_CATEGORY_COLUMN] = df[MAIN_CATEGORY_COLUMN].apply(clean_text)

    if CURATED_FLAG_COLUMN not in df.columns:
        df[CURATED_FLAG_COLUMN] = "no"
    else:
        df[CURATED_FLAG_COLUMN] = df[CURATED_FLAG_COLUMN].apply(clean_text)

    curated_indices = []

    print("Starting manual curation...\n")

    for subcategory, (new_main_category, requested_n) in CURATION_PLAN.items():
        if new_main_category == "TODO_MAIN_CATEGORY":
            print(f"[SKIP] {subcategory}: target main category not set yet")
            continue

        # Only curate rows where:
        # 1) subcategory matches
        # 2) main category is currently empty/unmapped
        eligible_mask = (
            (df[SUBCATEGORY_COLUMN] == clean_text(subcategory))
            & (df[MAIN_CATEGORY_COLUMN].apply(is_empty_label))
        )

        eligible_indices = df.index[eligible_mask].tolist()
        eligible_n = len(eligible_indices)

        # Optional info: how many rows of that subcategory already had a main category
        total_subcategory_n = len(df.index[df[SUBCATEGORY_COLUMN] == clean_text(subcategory)])
        already_mapped_n = total_subcategory_n - eligible_n

        if eligible_n == 0:
            print(
                f"[WARN] No eligible unmapped rows found for subcategory: {subcategory} "
                f"(already mapped rows: {already_mapped_n})"
            )
            continue

        actual_n = min(requested_n, eligible_n)

        sampled_indices = (
            pd.Series(eligible_indices)
            .sample(n=actual_n, random_state=RANDOM_STATE)
            .tolist()
        )

        df.loc[sampled_indices, MAIN_CATEGORY_COLUMN] = clean_text(new_main_category)
        df.loc[sampled_indices, CURATED_FLAG_COLUMN] = "yes"
        curated_indices.extend(sampled_indices)

        print(
            f"[OK] {subcategory} -> {new_main_category} | "
            f"requested={requested_n}, eligible_unmapped={eligible_n}, "
            f"already_mapped={already_mapped_n}, curated={actual_n}"
        )

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nCuration completed.")
    print(f"Total curated rows: {len(curated_indices)}")
    print(f"Saved file: {OUTPUT_FILE}")
    print("\nCurated rows by flag:")
    print(df[CURATED_FLAG_COLUMN].value_counts())

    print("\nSample curated rows:")
    curated_sample = df[df[CURATED_FLAG_COLUMN] == "yes"][
        [SUBCATEGORY_COLUMN, MAIN_CATEGORY_COLUMN, CURATED_FLAG_COLUMN]
    ].head(20)
    print(curated_sample)


if __name__ == "__main__":
    main()