from pathlib import Path


APP_NAME = "Project GENESIS"

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"

DEFAULT_DISEASE_QUERY = "Parkinson disease"
DEFAULT_YEARS_BACK = 5
DEFAULT_MAX_RESULTS = 100