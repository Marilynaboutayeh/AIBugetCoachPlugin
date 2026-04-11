from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[4]
# DATA_DIR = BASE_DIR / "data"
DATA_DIR = BASE_DIR / "shared" / "data"


def normalize_mcc(mcc) -> str | None:
    if mcc is None:
        return None

    mcc_str = str(mcc).strip()
    if not mcc_str.isdigit():
        return None

    return mcc_str.zfill(4)


def load_main_category_rules():
    path = DATA_DIR / "digital_bank_categories.csv"
    df = pd.read_csv(path)

    return df.to_dict(orient="records")


def load_subcategory_rules():
    path = DATA_DIR / "mcc_range_to_subcategory.csv"
    df = pd.read_csv(path)

    return df.to_dict(orient="records")


def load_sub_subcategory_rules():
    path = DATA_DIR / "mcc_to_sub_subcategory.csv"
    df = pd.read_csv(path, dtype={"mcc": str})
    df["mcc"] = df["mcc"].apply(normalize_mcc)

    return df.to_dict(orient="records")

def normalize_label(value) -> str:
    if value is None:
        return ""

    return " ".join(str(value).strip().lower().split())


def load_sub_subcategory_to_digital_bank_rules():
    path = DATA_DIR / "sub_subcategory_to_digital_bank_categories.csv"
    df = pd.read_csv(path, dtype={"mcc": str})

    if "sub_subcategory" in df.columns:
        df["sub_subcategory"] = df["sub_subcategory"].apply(normalize_label)

    return df.to_dict(orient="records")