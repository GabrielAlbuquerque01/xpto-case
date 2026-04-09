from pathlib import Path
from dotenv import load_dotenv
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "")

DATA_PATH = BASE_DIR / "data" / "dataset.csv"
ARTIFACTS_DIR = BASE_DIR / "app" / "artifacts"

DATABASE_URL = os.getenv("DATABASE_URL", "")
API_HOST = os.getenv("API_HOST", "http://localhost:8000")