from pathlib import Path

# Base paths
ML_FALLBACK_DIR = Path(__file__).resolve().parent
CATEGORIZATION_DIR = ML_FALLBACK_DIR.parent
SERVICES_DIR = CATEGORIZATION_DIR.parent
APP_DIR = SERVICES_DIR.parent
BACKEND_DIR = APP_DIR.parent

# Input dataset
# TRAINING_DATA_FILE = BACKEND_DIR / "categorized_output.csv"
# TRAINING_DATA_FILE = BACKEND_DIR / "categorized_curated.csv"
TRAINING_DATA_FILE = BACKEND_DIR / "categorized_curated_with_subsub_mapping.csv"

# Output artifacts
ARTIFACTS_DIR = ML_FALLBACK_DIR / "artifacts"
MODEL_FILE = ARTIFACTS_DIR / "main_category_model.joblib"

# Target column
TARGET_COLUMN = "predicted_main_category"

# Input feature columns in raw dataset
TEXT_COLUMNS = [
    "merchant_description",
    "merchant_token",
]

CATEGORICAL_COLUMNS = [
    "predicted_subcategory",
    # "predicted_sub_subcategory",
    "city",
    "country",
]

NUMERIC_COLUMNS = [
    "amount",
]

DATE_COLUMNS = [
    "date",
]

# Prediction settings
ML_CONFIDENCE_THRESHOLD = 0.70
RANDOM_STATE = 42
TEST_SIZE = 0.2