import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the current directory or project root
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()


class Settings:
    # Project Info
    PROJECT_NAME: str = "FISHER AI CCTV Backend Service"
    PROJECT_VERSION: str = "1.0.0"

    # Telegram Credentials
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
    CHAT_ID: str = os.getenv("CHAT_ID", "").strip()

    # MongoDB Atlas
    MONGODB_URI: str = os.getenv(
        "MONGODB_URI",
        "mongodb+srv://hawletmusbah_db_user:puUdN6mm658u5zPb@cluster0.cnbvulh.mongodb.net/?retryWrites=true&w=majority",
    ).strip()
    DB_NAME: str = os.getenv("DB_NAME", "fisher_cctv").strip()

    # Backend Server
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", 8000))
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    API_DETECTIONS_URL: str = os.getenv(
        "API_DETECTIONS_URL", f"{API_BASE_URL}/api/detections"
    )

    # Directories
    OUTPUT_DIR: Path = BASE_DIR / "output"
    INTRUSIONS_DIR: Path = OUTPUT_DIR / "intrusions"

    # Alert & Video Parameters (Exactly 2-minute video recording)
    INTRUSION_VIDEO_SECONDS: int = int(os.getenv("INTRUSION_VIDEO_SECONDS", "120"))

    # Authorized Users (Exactly 3 permitted accounts)
    _raw_emails = os.getenv(
        "AUTHORIZED_EMAILS",
        "admin@fisher.cctv,operator@fisher.cctv,supervisor@fisher.cctv",
    )
    AUTHORIZED_EMAILS: list[str] = [
        email.strip().lower() for email in _raw_emails.split(",") if email.strip()
    ]

    # CORS
    _raw_cors = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    )
    CORS_ORIGINS: list[str] = [origin.strip() for origin in _raw_cors.split(",") if origin.strip()]


settings = Settings()
