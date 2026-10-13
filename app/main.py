from fastapi import FastAPI

from app.routers import users
from app.routers import cameras
from app.routers import detections
from app.routers import events
from app.routers import alerts


app = FastAPI(
    title="FISHER AI CCTV SYSTEM",
    description="AI-powered CCTV monitoring backend",
    version="1.0.0",
)


app.include_router(users.router)
app.include_router(cameras.router)
app.include_router(detections.router)
app.include_router(events.router)
app.include_router(alerts.router)


@app.get("/")
def root():
    return {
        "system": "FISHER AI CCTV SYSTEM",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "api": "running",
        "database": "connected"
    }
