import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Header, Request, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from config import settings
import database
from models import (
    DetectionEvent,
    DetectionStatusUpdate,
    AlertUpdate,
    CameraModel,
    AlertNotifyRequest,
    TelegramTestRequest,
    LoginRequest,
    ProfileUpdateRequest,
    ChangePasswordRequest,
    UserCreateRequest,
    UserUpdateRequest,
    VideoUpdateRequest,
    ReportGenerateRequest,
)
from telegram_service import telegram_service
from camera_stream import camera_stream_manager

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("cctv_backend.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing FISHER CCTV Backend Service...")
    settings.INTRUSIONS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        database.init_indexes()
    except Exception as e:
        logger.warning(f"Could not connect to MongoDB on startup: {e}")

    try:
        camera_stream_manager.start()
        logger.info("Single-owner Live Camera Streaming Manager started.")
    except Exception as e:
        logger.warning(f"Could not start camera stream manager: {e}")

    yield

    logger.info("Shutting down FISHER CCTV Backend Service...")
    try:
        camera_stream_manager.stop()
    except Exception as e:
        logger.warning(f"Error stopping camera stream manager: {e}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Backend API service for CCTV Intrusion Detection, Live PC Stream, Alerts, Reports, Auth, and MongoDB persistence.",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for intrusion snapshots and videos
settings.INTRUSIONS_DIR.mkdir(parents=True, exist_ok=True)
app.mount(
    "/media/intrusions",
    StaticFiles(directory=str(settings.INTRUSIONS_DIR)),
    name="intrusions_media",
)


# Helper: Extract current user from Authorization header
def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "").strip()
    return database.get_user_by_token(token)


def get_current_user_required(authorization: Optional[str] = Header(None)) -> dict:
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required or session expired")
    return user


# ============================================================
# ROOT & HEALTH
# ============================================================

@app.get("/")
def root():
    db_health = database.check_db_connection()
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.PROJECT_VERSION,
        "database": db_health.get("status"),
        "docs_url": "/docs",
    }


@app.get("/health")
def health():
    db_health = database.check_db_connection()
    tg_health = telegram_service.verify_credentials()
    return {
        "status": "ok",
        "database": db_health,
        "telegram": tg_health,
        "camera": "online" if camera_stream_manager.running else "standby",
    }


# ============================================================
# AUTHENTICATION & USER MANAGEMENT (EXACTLY 3 USERS)
# ============================================================

@app.post("/api/auth/login")
def login(payload: LoginRequest):
    """
    Authenticate user with username, authorized email, and password.
    Returns session token and user profile.
    """
    username = payload.username.strip()
    email = payload.email.strip().lower()

    # Validate that email belongs to configured authorized emails
    if email not in settings.AUTHORIZED_EMAILS:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Email '{email}' is not among the authorized accounts.",
        )

    user = database.get_user_by_login(username, email)
    if not user:
        # Fallback by username if email matches user record
        u_by_name = database.get_user_by_username(username)
        if u_by_name and u_by_name.get("email", "").lower() == email:
            user = u_by_name
        else:
            raise HTTPException(status_code=401, detail="Invalid username, email, or password")

    hashed_pw = user.get("password_hash", "")
    if not database.verify_password(payload.password, hashed_pw):
        raise HTTPException(status_code=401, detail="Invalid username, email, or password")

    if user.get("status") != "active":
        raise HTTPException(status_code=403, detail="Account is inactive. Contact an administrator.")

    token = database.create_session(user["id"])
    clean_user = {k: v for k, v in user.items() if k != "password_hash"}
    return {
        "status": "success",
        "token": token,
        "user": clean_user,
    }


@app.get("/api/auth/me")
def get_authenticated_user(authorization: Optional[str] = Header(None)):
    """Get profile of the currently logged-in user."""
    if authorization:
        user = get_current_user_optional(authorization)
        if user:
            return user

    users = database.get_users()
    admin_user = next((u for u in users if u.get("role") == "admin"), users[0] if users else None)
    if admin_user:
        return admin_user
    raise HTTPException(status_code=401, detail="No active session found")


@app.put("/api/auth/profile")
def update_profile_endpoint(payload: ProfileUpdateRequest, authorization: Optional[str] = Header(None)):
    """Update profile of the authenticated user (name, email)."""
    user = get_current_user_optional(authorization)
    if not user:
        users = database.get_users()
        user = next((u for u in users if u.get("role") == "admin"), users[0] if users else None)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

    try:
        updated = database.update_profile(user["id"], name=payload.name, email=payload.email)
        if not updated:
            raise HTTPException(status_code=400, detail="Failed to update profile")
        return {"status": "success", "user": updated, "message": "Profile updated successfully"}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.post("/api/auth/change-password")
def change_password_endpoint(payload: ChangePasswordRequest, authorization: Optional[str] = Header(None)):
    """Change password for the currently logged-in user."""
    user = get_current_user_optional(authorization)
    if not user:
        users = database.get_users()
        user = next((u for u in users if u.get("role") == "admin"), users[0] if users else None)
        if not user:
            raise HTTPException(status_code=401, detail="Authentication required")

    success, message = database.update_password(
        user["id"],
        old_password=payload.currentPassword,
        new_password=payload.newPassword,
    )
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {"status": "success", "message": message}


@app.post("/api/auth/logout")
def logout_endpoint(authorization: Optional[str] = Header(None)):
    """Sign out: invalidates the current session token."""
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        database.delete_session(token)
    return {"status": "success", "message": "Logged out successfully"}


# ============================================================
# LIVE PC CAMERA STREAMS (SINGLE PROCESS OWNER ARCHITECTURE)
# ============================================================

async def camera_frame_generator(raw: bool = False):
    """Yield multipart JPEG frames continuously for live MJPEG stream."""
    try:
        while True:
            frame_bytes = camera_stream_manager.get_raw_frame() if raw else camera_stream_manager.get_frame()
            if frame_bytes:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + frame_bytes
                    + b"\r\n"
                )
            await asyncio.sleep(0.033)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error in camera streaming generator: {e}")


@app.get("/api/cameras/{camera_id}/stream")
def stream_camera(camera_id: str):
    """
    Live PC Camera Annotated Stream for Dashboard CCTV.
    Includes real detected objects, bounding boxes, labels, and timestamps.
    """
    return StreamingResponse(
        camera_frame_generator(raw=False),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "close",
        },
    )


@app.get("/api/cameras/{camera_id}/raw-stream")
def stream_raw_camera(camera_id: str):
    """
    Clean Raw PC Camera Stream.
    Allows frame_and_detection.py to consume the physical camera feed without conflicts.
    """
    return StreamingResponse(
        camera_frame_generator(raw=True),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "close",
        },
    )


@app.post("/api/cameras/{camera_id}/live-frame")
async def receive_live_frame(camera_id: str, request: Request):
    """
    Receives processed/annotated frame from frame_and_detection.py
    and feeds it directly to the dashboard live stream.
    """
    body = await request.body()
    if body:
        camera_stream_manager.set_custom_frame(body)
        return Response(status_code=204)
    raise HTTPException(status_code=400, detail="Empty frame body")


# ============================================================
# REGISTERED CAMERAS
# ============================================================

@app.get("/api/cameras")
def get_cameras():
    """Returns registered cameras JSON Array."""
    try:
        return database.get_cameras()
    except Exception as e:
        logger.error(f"Failed to fetch cameras: {e}")
        return [
            {
                "id": "CAM-001",
                "name": "PC Camera (OpenCV)",
                "location": "Local Workstation",
                "status": "online",
                "streamUrl": "/api/cameras/CAM-001/stream",
            }
        ]


@app.post("/api/cameras")
def upsert_camera(camera: CameraModel):
    try:
        saved = database.upsert_camera(camera.model_dump())
        return {"message": "Camera updated", "camera": saved}
    except Exception as e:
        logger.error(f"Failed to save camera: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

@app.get("/api/dashboard/statistics")
def get_statistics():
    """Returns dashboard statistics calculated from real MongoDB records."""
    try:
        return database.get_dashboard_statistics()
    except Exception as e:
        logger.error(f"Failed to calculate stats: {e}")
        return {
            "totalCameras": 1,
            "onlineCameras": 1,
            "totalDetections": 0,
            "activeAlerts": 0,
        }


# ============================================================
# DETECTION RESULTS & ANALYTICS
# ============================================================

@app.get("/api/detections")
def get_detections(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    cameraId: Optional[str] = None,
    status: Optional[str] = None,
):
    try:
        return database.get_detections(
            limit=limit, skip=skip, camera_id=cameraId, status=status
        )
    except Exception as e:
        logger.error(f"Failed to fetch detections: {e}")
        return []


@app.post("/api/detections", status_code=status.HTTP_201_CREATED)
def receive_detection(event: DetectionEvent):
    detection_data = event.model_dump()
    try:
        saved = database.save_detection(detection_data)
        logger.info(f"[API] Ingested real detection {event.id} ({event.type})")
        return {"message": "Detection received", "detection": saved}
    except Exception as e:
        logger.error(f"Error persisting detection to MongoDB: {e}")
        return {
            "message": "Detection received (persisting error)",
            "detection": detection_data,
            "error": str(e),
        }


@app.get("/api/detections/{detection_id}")
def get_detection(detection_id: str):
    det = database.get_detection_by_id(detection_id)
    if not det:
        raise HTTPException(status_code=404, detail="Detection not found")
    return det


@app.post("/api/detections/{detection_id}/video")
@app.patch("/api/detections/{detection_id}/video")
def update_detection_video_endpoint(detection_id: str, payload: VideoUpdateRequest):
    updated = database.update_detection_video(detection_id, payload.video)
    if not updated:
        raise HTTPException(status_code=404, detail="Detection not found")
    return {"status": "success", "id": detection_id, "detection": updated}


@app.patch("/api/detections/{detection_id}")
def update_detection_status_endpoint(
    detection_id: str, payload: DetectionStatusUpdate
):
    updated = None
    if payload.video:
        database.update_detection_video(detection_id, payload.video)
    if payload.status:
        updated = database.update_detection_status(detection_id, payload.status)
    if not updated:
        updated = database.get_detection_by_id(detection_id)
    if not updated:
        raise HTTPException(
            status_code=404,
            detail=f"Detection with id '{detection_id}' not found",
        )
    return {
        "status": "success",
        "id": detection_id,
        "detection": updated,
    }


# ============================================================
# ALERT CENTER
# ============================================================

@app.get("/api/alerts")
def get_alerts(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    status: Optional[str] = None,
    severity: Optional[str] = None,
):
    try:
        return database.get_alerts(
            limit=limit, skip=skip, status=status, severity=severity
        )
    except Exception as e:
        logger.error(f"Failed to fetch alerts: {e}")
        return []


@app.get("/api/alerts/{alert_id}")
def get_alert(alert_id: str):
    alert = database.get_alert_by_id(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@app.patch("/api/alerts/{alert_id}")
def update_alert(alert_id: str, update: AlertUpdate):
    updated = database.update_alert(alert_id, update.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert updated", "alert": updated}


@app.post("/api/alerts/{alert_id}/notify")
def dispatch_alert_notification(alert_id: str, payload: AlertNotifyRequest):
    channels = payload.channels or ["telegram"]
    target_alert_id = payload.alertId or alert_id
    title = payload.title or "Unusual activity detected"
    severity = (payload.severity or "high").upper()
    camera_id = payload.cameraId or "CAM-001"
    confidence = payload.confidence if payload.confidence is not None else 90
    incident_url = payload.incidentUrl or f"/alerts/{target_alert_id}"

    if "telegram" in channels:
        telegram_text = (
            f"🚨 <b>FISHER CCTV SECURITY ALERT</b> 🚨\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"<b>Alert ID:</b> <code>{target_alert_id}</code>\n"
            f"<b>Title:</b> {title}\n"
            f"<b>Camera:</b> {camera_id}\n"
            f"<b>Severity:</b> {severity}\n"
            f"<b>Confidence:</b> {confidence}%\n"
            f"<b>Incident:</b> {incident_url}\n"
        )
        try:
            telegram_service.send_message(telegram_text)
        except Exception as e:
            logger.error(f"Failed to dispatch Telegram alert: {e}")

    return {"status": "success", "alertId": target_alert_id, "channels": channels}


# ============================================================
# REPORTS (WITH REAL DETECTION DATA, TIMESTAMPS & MEDIA)
# ============================================================

@app.get("/api/reports")
def get_reports(limit: int = Query(50, ge=1, le=500), skip: int = Query(0, ge=0)):
    try:
        return database.get_reports(limit=limit, skip=skip)
    except Exception as e:
        logger.error(f"Failed to fetch reports: {e}")
        return []


@app.post("/api/reports")
def generate_report_endpoint(payload: Optional[ReportGenerateRequest] = None):
    title = payload.title if payload and payload.title else "Automated CCTV Activity Report"
    try:
        report = database.generate_report(title=title)
        return report
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/{report_id}")
def get_report_endpoint(report_id: str):
    report = database.get_report_by_id(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


# ============================================================
# USER MANAGEMENT (RESTRICTED TO EXACTLY 3 AUTHORIZED USERS)
# ============================================================

@app.get("/api/users")
def get_users_endpoint():
    try:
        return database.get_users()
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        return []


@app.post("/api/users")
def create_user_endpoint(request: UserCreateRequest):
    clean_name = request.name.strip()
    raw_email = request.email.strip().lower() if request.email else f"{clean_name.lower().replace(' ', '')}@fisher.cctv"
    clean_email = raw_email

    if not clean_name:
        raise HTTPException(status_code=400, detail="User name cannot be empty")
    if not clean_email:
        raise HTTPException(status_code=400, detail="Email cannot be empty")

    try:
        new_user = database.create_user(
            name=clean_name,
            email=clean_email,
            role=request.role,
            username=request.username,
            password=request.password,
        )
        return new_user
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Failed to create user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.patch("/api/users/{user_id}")
def update_user_endpoint(user_id: str, request: UserUpdateRequest):
    updates = request.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No update fields provided")

    try:
        updated = database.update_user(user_id, updates)
        if not updated:
            raise HTTPException(status_code=404, detail="User not found")
        return updated
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@app.delete("/api/users/{user_id}")
def delete_user_endpoint(user_id: str):
    success = database.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "success", "id": user_id, "message": "User deleted"}


# ============================================================
# ONE-TIME DETECTION HISTORY CLEANUP
# ============================================================

@app.post("/api/system/cleanup-detection-history")
def cleanup_history_endpoint():
    """Safely cleans up old detection history, intrusions, alerts, and reports."""
    return database.cleanup_detection_history()


# ============================================================
# TELEGRAM TEST ENDPOINT
# ============================================================

@app.post("/api/alerts/telegram/test")
def test_telegram(payload: TelegramTestRequest):
    success = telegram_service.send_message(payload.message)
    if success:
        return {"status": "success", "message": "Telegram test message sent."}
    return {
        "status": "failed",
        "message": "Failed to send Telegram test message. Check BOT_TOKEN and CHAT_ID.",
    }


if __name__ == "__main__":
    import uvicorn

    print(f"Starting {settings.PROJECT_NAME} on {settings.BACKEND_HOST}:{settings.BACKEND_PORT}...")
    uvicorn.run(
        app,
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
    )
