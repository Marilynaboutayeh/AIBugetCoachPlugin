from pathlib import Path
import pandas as pd


# BASE_DIR = Path(__file__).resolve().parents[4]
# DATA_DIR = BASE_DIR / "data"
# MAPPING_FILE = DATA_DIR / "sub_subcategory_to_digital_bank_categories.csv"

ROOT_DIR = Path(__file__).resolve().parents[5]
MAPPING_FILE = ROOT_DIR / "shared" / "data" / "sub_subcategory_to_digital_bank_categories.csv"

def load_subsubcategory_to_main_category_mapping() -> dict[str, str]:
    df = pd.read_csv(MAPPING_FILE)

    sub_sub_col = "sub_subcategory"
    main_col = "digital_banking_category"

    df[sub_sub_col] = df[sub_sub_col].astype(str).str.strip()
    df[main_col] = df[main_col].astype(str).str.strip()

    df = df[
        (df[sub_sub_col] != "") &
        (df[main_col] != "") &
        (df[sub_sub_col].str.lower() != "nan") &
        (df[main_col].str.lower() != "nan")
    ].copy()

    return dict(zip(df[sub_sub_col], df[main_col]))