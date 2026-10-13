from typing import Optional
from pathlib import Path
import json

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from alerts import AlertManager
from alerts.models import AlertEvent


BASE_DIR = Path(__file__).resolve().parent

LOG_FILE = BASE_DIR / "logs" / "alerts.jsonl"
SCREENSHOT_DIR = BASE_DIR / "screenshots"
DASHBOARD_FILE = BASE_DIR / "dashboard.html"


app = FastAPI(
    title="FISHER Alert Layer",
    description="Security alert API for the FISHER system",
    version="1.0.0"
)

manager = AlertManager()


class AlertRequest(BaseModel):
    event_type: str
    camera: str
    confidence: float
    timestamp: str
    severity: str = "HIGH"
    screenshot_path: Optional[str] = None
    message: Optional[str] = None


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "FISHER Alert Layer"
    }


@app.post("/alerts")
def create_alert(payload: AlertRequest):
    event = AlertEvent(
        event_type=payload.event_type,
        camera=payload.camera,
        confidence=payload.confidence,
        timestamp=payload.timestamp,
        severity=payload.severity,
        screenshot_path=payload.screenshot_path,
        message=payload.message
    )

    return manager.send_alert(event)


@app.get("/alerts")
def get_alerts():
    alerts = []

    if LOG_FILE.exists():
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()

                if not line:
                    continue

                try:
                    alerts.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    alerts.reverse()

    return {
        "count": len(alerts),
        "alerts": alerts
    }


@app.get("/screenshots/{filename}")
def get_screenshot(filename: str):
    file_path = SCREENSHOT_DIR / filename

    if not file_path.exists():
        return {"error": "Screenshot not found"}

    if not file_path.is_file():
        return {"error": "Invalid screenshot"}

    return FileResponse(file_path)


@app.get("/dashboard")
def dashboard():
    if not DASHBOARD_FILE.exists():
        return {"error": "dashboard.html not found"}

    return FileResponse(DASHBOARD_FILE)
