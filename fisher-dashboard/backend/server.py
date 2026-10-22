import os
import sys
from pathlib import Path

# Add 'finals' directory to sys.path so detection_api, database, config, etc. can be resolved
FINALS_DIR = Path(__file__).resolve().parents[2] / "finals"
if not FINALS_DIR.exists():
    # Fallback to relative path lookup
    FINALS_DIR = Path("C:/Users/Lenovo/Desktop/ending/finals")

if str(FINALS_DIR) not in sys.path:
    sys.path.insert(0, str(FINALS_DIR))

from detection_api import app

if __name__ == "__main__":
    import uvicorn
    from config import settings

    print(f"Starting unified FISHER Backend Service on {settings.BACKEND_HOST}:{settings.BACKEND_PORT}...")
    uvicorn.run(app, host=settings.BACKEND_HOST, port=settings.BACKEND_PORT)
