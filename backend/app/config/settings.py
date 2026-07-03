from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
PROJECT_DIR = BASE_DIR.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = PROJECT_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"
DATABASE_URL = f"sqlite:///{(BASE_DIR / 'omnidocs.db').as_posix()}"
API_PREFIX = "/api"

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

for directory in (UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR):
    directory.mkdir(parents=True, exist_ok=True)
