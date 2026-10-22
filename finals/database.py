import os
import json
import logging
import re
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import bcrypt
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import ConnectionFailure, PyMongoError

from config import settings

logger = logging.getLogger("cctv_backend.database")

# Initialize MongoDB client
_client: Optional[MongoClient] = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                retryWrites=True,
                w="majority",
            )
        except Exception as e:
            logger.error(f"Failed to create MongoClient: {e}")
            raise
    return _client


def get_db():
    client = get_client()
    return client[settings.DB_NAME]


def check_db_connection() -> Dict[str, Any]:
    """Test ping to MongoDB."""
    try:
        client = get_client()
        result = client.admin.command("ping")
        db = get_db()
        collections = db.list_collection_names()
        return {
            "status": "connected",
            "ping": bool(result.get("ok")),
            "database": settings.DB_NAME,
            "collections": collections,
        }
    except Exception as e:
        logger.error(f"MongoDB connection check failed: {e}")
        return {
            "status": "disconnected",
            "error": str(e),
            "database": settings.DB_NAME,
        }


def init_indexes():
    """Ensure indexes on all collections and run initial migrations."""
    try:
        db = get_db()
        # Detections
        db.detections.create_index([("id", ASCENDING)], unique=True)
        db.detections.create_index([("timestamp", DESCENDING)])
        db.detections.create_index([("cameraId", ASCENDING)])
        db.detections.create_index([("status", ASCENDING)])

        # Alerts
        db.alerts.create_index([("id", ASCENDING)], unique=True)
        db.alerts.create_index([("timestamp", DESCENDING)])
        db.alerts.create_index([("status", ASCENDING)])
        db.alerts.create_index([("severity", ASCENDING)])

        # Cameras
        db.cameras.create_index([("id", ASCENDING)], unique=True)

        # Intrusions
        db.intrusions.create_index([("timestamp", DESCENDING)])
        db.intrusions.create_index([("track_id", ASCENDING)])

        # Users
        db.users.create_index([("id", ASCENDING)], unique=True)
        db.users.create_index([("username", ASCENDING)], unique=True)
        db.users.create_index([("email", ASCENDING)], unique=True)

        # Reports
        db.reports.create_index([("id", ASCENDING)], unique=True)
        db.reports.create_index([("createdAt", DESCENDING)])

        # Sessions
        db.sessions.create_index([("token", ASCENDING)], unique=True)

        # Ensure default camera exists and matches contract
        seed_default_camera()

        # Ensure authorized users exist
        seed_default_user()

        logger.info("MongoDB indexes successfully created/verified.")
    except Exception as e:
        logger.warning(f"Could not initialize indexes: {e}")


def seed_default_camera():
    """Ensure at least CAM-001 exists in database matching the frontend contract."""
    try:
        db = get_db()
        default_cam = {
            "id": "CAM-001",
            "name": "PC Camera (OpenCV)",
            "location": "Local Workstation",
            "status": "online",
            "streamUrl": "/api/cameras/CAM-001/stream",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        db.cameras.update_one(
            {"id": "CAM-001"},
            {"$set": default_cam},
            upsert=True,
        )
        logger.info("Seeded/updated default camera CAM-001.")
    except Exception as e:
        logger.warning(f"Failed to seed default camera: {e}")


def seed_default_user():
    """Ensure exactly the 3 authorized users exist in database."""
    try:
        db = get_db()
        default_accounts = [
            {
                "id": "USR-001",
                "username": "admin",
                "name": "Administrator",
                "email": "admin@fisher.cctv",
                "role": "admin",
                "password": "admin123",
            },
            {
                "id": "USR-002",
                "username": "operator",
                "name": "Control Operator",
                "email": "operator@fisher.cctv",
                "role": "operator",
                "password": "operator123",
            },
            {
                "id": "USR-003",
                "username": "supervisor",
                "name": "Security Supervisor",
                "email": "supervisor@fisher.cctv",
                "role": "operator",
                "password": "supervisor123",
            },
        ]

        auth_emails = settings.AUTHORIZED_EMAILS
        for idx, acc in enumerate(default_accounts):
            if idx < len(auth_emails):
                acc["email"] = auth_emails[idx]

            existing = db.users.find_one({
                "$or": [{"username": acc["username"]}, {"email": acc["email"]}]
            })
            if not existing:
                salt = bcrypt.gensalt()
                pwd_hash = bcrypt.hashpw(acc["password"].encode("utf-8"), salt).decode("utf-8")
                doc = {
                    "id": acc["id"],
                    "username": acc["username"],
                    "name": acc["name"],
                    "email": acc["email"],
                    "role": acc["role"],
                    "status": "active",
                    "password_hash": pwd_hash,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                db.users.insert_one(doc)
                logger.info(f"Seeded authorized user: {acc['username']} ({acc['email']})")
    except Exception as e:
        logger.warning(f"Failed to seed authorized users: {e}")


def _serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to convert MongoDB _id to string for JSON serialization."""
    if not doc:
        return doc
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc


# ============================================================
# DETECTIONS
# ============================================================

def save_detection(detection_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save a detection event and automatically create/update the corresponding alert.
    Captures both image snapshot and video file references.
    """
    db = get_db()
    det_id = detection_data["id"]

    img = detection_data.get("image")
    vid = detection_data.get("video")
    desc = detection_data.get("description", "")
    if not img and desc:
        m = re.search(r"Image:\s*([^\s;]+)", desc)
        if m:
            img = m.group(1)
    if not vid and desc:
        m = re.search(r"Video:\s*([^\s;]+)", desc)
        if m:
            vid = m.group(1)

    detection_doc = {**detection_data}
    if "status" not in detection_doc or detection_doc["status"] == "open":
        detection_doc["status"] = "new"

    if "created_at" not in detection_doc:
        detection_doc["created_at"] = datetime.now(timezone.utc).isoformat()

    if img:
        detection_doc["image"] = img
        detection_doc["imageUrl"] = f"/media/intrusions/{img}"
    if vid:
        detection_doc["video"] = vid
        detection_doc["videoUrl"] = f"/media/intrusions/{vid}"

    db.detections.update_one(
        {"id": det_id},
        {"$set": detection_doc},
        upsert=True,
    )

    alert_doc = {
        "id": det_id,
        "title": detection_data.get("type", "Person detected"),
        "description": desc or "Person detected in camera field of view.",
        "confidence": detection_data.get("confidence", 0.0),
        "severity": detection_data.get("severity", "high"),
        "status": "open" if detection_doc["status"] == "new" else detection_doc["status"],
        "timestamp": detection_data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "cameraId": detection_data.get("cameraId", "CAM-001"),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    if img:
        alert_doc["image"] = img
        alert_doc["imageUrl"] = f"/media/intrusions/{img}"
    if vid:
        alert_doc["video"] = vid
        alert_doc["videoUrl"] = f"/media/intrusions/{vid}"

    db.alerts.update_one(
        {"id": det_id},
        {"$set": alert_doc},
        upsert=True,
    )

    return _serialize_doc(detection_doc)


def get_detections(
    limit: int = 50,
    skip: int = 0,
    camera_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    db = get_db()
    query: Dict[str, Any] = {}
    if camera_id:
        query["cameraId"] = camera_id
    if status:
        query["status"] = status

    cursor = (
        db.detections.find(query)
        .sort("timestamp", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    detections = []
    for doc in cursor:
        d = _serialize_doc(doc)
        if d.get("status") in ["open", None]:
            d["status"] = "new"
        try:
            d["confidence"] = round(float(d.get("confidence", 95)), 1)
        except Exception:
            d["confidence"] = 95
        if d.get("severity") not in ["low", "medium", "high", "critical"]:
            d["severity"] = "high"

        img = d.get("image")
        vid = d.get("video")
        desc = d.get("description", "")
        if not img and desc:
            m = re.search(r"Image:\s*([^\s;]+)", desc)
            if m:
                img = m.group(1)
        if not vid and desc:
            m = re.search(r"Video:\s*([^\s;]+)", desc)
            if m:
                vid = m.group(1)
        if img:
            d["image"] = img
            d["imageUrl"] = f"/media/intrusions/{img}"
        if vid:
            d["video"] = vid
            d["videoUrl"] = f"/media/intrusions/{vid}"

        detections.append(d)
    return detections


def get_detection_by_id(det_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.detections.find_one({"id": det_id})
    if not doc:
        return None
    d = _serialize_doc(doc)
    if d.get("status") in ["open", None]:
        d["status"] = "new"
    return d


def update_detection_status(detection_id: str, new_status: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    if new_status == "open":
        new_status = "new"
    elif new_status == "resolved":
        new_status = "reviewed"

    now_iso = datetime.now(timezone.utc).isoformat()
    result = db.detections.find_one_and_update(
        {"id": detection_id},
        {"$set": {"status": new_status, "updated_at": now_iso}},
        return_document=True,
    )
    if result:
        alert_status = "open" if new_status == "new" else new_status
        db.alerts.update_one(
            {"id": detection_id},
            {"$set": {"status": alert_status, "updated_at": now_iso}},
        )
        return _serialize_doc(result)
    return None


def update_detection_video(detection_id: str, video_filename: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    video_url = f"/media/intrusions/{video_filename}"
    updates = {
        "video": video_filename,
        "videoUrl": video_url,
        "video_ready": True,
        "updated_at": now_iso,
    }
    det = db.detections.find_one_and_update(
        {"id": detection_id},
        {"$set": updates},
        return_document=True,
    )
    db.alerts.update_one(
        {"id": detection_id},
        {"$set": {"video": video_filename, "videoUrl": video_url, "updated_at": now_iso}},
    )
    db.intrusions.update_one(
        {"id": detection_id},
        {"$set": {"video": video_filename, "video_ready": True}},
    )
    logger.info(f"Updated detection & alert {detection_id} with completed video {video_filename}")
    return _serialize_doc(det) if det else None


# ============================================================
# ALERTS
# ============================================================

def get_alerts(
    limit: int = 50,
    skip: int = 0,
    status: Optional[str] = None,
    severity: Optional[str] = None,
) -> List[Dict[str, Any]]:
    db = get_db()
    query: Dict[str, Any] = {}
    if status:
        query["status"] = status
    if severity:
        query["severity"] = severity

    cursor = (
        db.alerts.find(query)
        .sort("timestamp", DESCENDING)
        .skip(skip)
        .limit(limit)
    )
    alerts = []
    for doc in cursor:
        a = _serialize_doc(doc)
        if "title" not in a or not a["title"]:
            a["title"] = a.get("type", "Unusual activity detected")
        if "description" not in a or not a["description"]:
            a["description"] = "Security event detected by camera."
        if "cameraId" not in a or not a["cameraId"]:
            a["cameraId"] = "CAM-001"
        try:
            a["confidence"] = round(float(a.get("confidence", 85)), 1)
        except Exception:
            a["confidence"] = 85
        if "status" not in a or not a["status"]:
            a["status"] = "open"

        img = a.get("image")
        vid = a.get("video")
        desc = a.get("description", "")
        if not img and desc:
            m = re.search(r"Image:\s*([^\s;]+)", desc)
            if m:
                img = m.group(1)
        if not vid and desc:
            m = re.search(r"Video:\s*([^\s;]+)", desc)
            if m:
                vid = m.group(1)
        if img:
            a["image"] = img
            a["imageUrl"] = f"/media/intrusions/{img}"
        if vid:
            a["video"] = vid
            a["videoUrl"] = f"/media/intrusions/{vid}"

        alerts.append(a)
    return alerts


def get_alert_by_id(alert_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.alerts.find_one({"id": alert_id})
    return _serialize_doc(doc) if doc else None


def update_alert(alert_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    result = db.alerts.find_one_and_update(
        {"id": alert_id},
        {"$set": updates},
        return_document=True,
    )
    if result and "status" in updates:
        det_status = updates["status"]
        if det_status == "open":
            det_status = "new"
        elif det_status == "resolved":
            det_status = "reviewed"
        db.detections.update_one(
            {"id": alert_id},
            {"$set": {"status": det_status}},
        )
    return _serialize_doc(result) if result else None


# ============================================================
# CAMERAS
# ============================================================

def get_cameras() -> List[Dict[str, Any]]:
    db = get_db()
    cameras = list(db.cameras.find())
    if not cameras:
        seed_default_camera()
        cameras = list(db.cameras.find())

    cleaned = []
    for cam in cameras:
        doc = _serialize_doc(cam)
        cam_id = doc.get("id", "CAM-001")
        cleaned.append({
            "id": cam_id,
            "name": doc.get("name", "PC Camera (OpenCV)"),
            "location": doc.get("location", "Local Workstation"),
            "status": doc.get("status", "online"),
            "streamUrl": doc.get("streamUrl", f"/api/cameras/{cam_id}/stream"),
        })
    return cleaned


def upsert_camera(camera_data: Dict[str, Any]) -> Dict[str, Any]:
    db = get_db()
    cam_id = camera_data["id"]
    if "streamUrl" not in camera_data or not camera_data["streamUrl"]:
        camera_data["streamUrl"] = f"/api/cameras/{cam_id}/stream"
    camera_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    db.cameras.update_one(
        {"id": cam_id},
        {"$set": camera_data},
        upsert=True,
    )
    doc = db.cameras.find_one({"id": cam_id})
    return _serialize_doc(doc)


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

def get_dashboard_statistics() -> Dict[str, Any]:
    db = get_db()
    total_cameras = db.cameras.count_documents({})
    online_cameras = db.cameras.count_documents({"status": "online"})
    total_detections = db.detections.count_documents({})
    active_alerts = db.alerts.count_documents({"status": {"$in": ["open", "new"]}})
    resolved_alerts = db.alerts.count_documents({"status": {"$in": ["resolved", "reviewed", "dismissed"]}})
    total_intrusions = db.intrusions.count_documents({})

    return {
        "totalCameras": max(1, total_cameras),
        "onlineCameras": max(1, online_cameras),
        "totalDetections": total_detections,
        "activeAlerts": active_alerts,
        "resolvedAlerts": resolved_alerts,
        "totalIntrusions": total_intrusions,
    }


# ============================================================
# CLEANUP DETECTION HISTORY ONLY
# ============================================================

def cleanup_detection_history() -> Dict[str, Any]:
    """
    Safely deletes old detection records, intrusions, alerts, and reports.
    Preserves users, auth sessions, and camera configurations.
    """
    db = get_db()
    det_res = db.detections.delete_many({})
    alt_res = db.alerts.delete_many({})
    int_res = db.intrusions.delete_many({})
    rep_res = db.reports.delete_many({})

    # Delete obsolete images and videos
    intrusions_dir = Path(settings.INTRUSIONS_DIR)
    deleted_files = 0
    if intrusions_dir.exists():
        for p in intrusions_dir.glob("*.*"):
            try:
                p.unlink()
                deleted_files += 1
            except Exception as e:
                logger.warning(f"Could not delete media file {p}: {e}")

    logger.info(
        f"Cleanup completed: {det_res.deleted_count} detections, "
        f"{alt_res.deleted_count} alerts, {int_res.deleted_count} intrusions, "
        f"{rep_res.deleted_count} reports, {deleted_files} media files removed."
    )
    return {
        "status": "success",
        "deleted_detections": det_res.deleted_count,
        "deleted_alerts": alt_res.deleted_count,
        "deleted_intrusions": int_res.deleted_count,
        "deleted_reports": rep_res.deleted_count,
        "deleted_files": deleted_files,
    }


def sync_disk_intrusions() -> Dict[str, Any]:
    """Scans output/intrusions for saved json intrusions and synchronizes them."""
    db = get_db()
    intrusions_dir = Path(settings.INTRUSIONS_DIR)
    if not intrusions_dir.exists():
        return {"synced": 0, "message": "Intrusions directory not found"}

    json_files = list(intrusions_dir.glob("*.json"))
    synced_count = 0

    for json_file in json_files:
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            timestamp = data.get("timestamp", "")
            track_id = data.get("track_id", "")
            clean_time = timestamp.replace(" ", "T").replace(":", "-")
            event_id = f"DET-{clean_time}-{track_id}"

            intrusion_doc = {
                "id": event_id,
                **data,
                "json_file": json_file.name,
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }
            db.intrusions.update_one(
                {"id": event_id},
                {"$set": intrusion_doc},
                upsert=True,
            )

            confidence_pct = round(float(data.get("confidence", 0.0)) * 100, 2)
            if confidence_pct <= 1.0:
                confidence_pct = confidence_pct * 100

            detection_doc = {
                "id": event_id,
                "cameraId": "CAM-001",
                "type": data.get("message", "Person entered the restricted area."),
                "confidence": confidence_pct,
                "severity": "high",
                "timestamp": timestamp,
                "status": "new",
                "description": (
                    f"Object: {data.get('object', 'person')}; "
                    f"Activity: {data.get('activity', 'restricted_area_intrusion')}; "
                    f"Track ID: {track_id}; "
                    f"Image: {data.get('image', '')}; "
                    f"Video: {data.get('video', '')}"
                ),
                "image": data.get("image"),
                "video": data.get("video"),
            }
            save_detection(detection_doc)
            synced_count += 1
        except Exception as e:
            logger.warning(f"Error syncing {json_file.name}: {e}")

    return {
        "synced": synced_count,
        "total_files": len(json_files),
        "message": f"Successfully synchronized {synced_count} intrusions to MongoDB",
    }


# ============================================================
# USERS & AUTHENTICATION
# ============================================================

def get_users() -> List[Dict[str, Any]]:
    db = get_db()
    users = list(db.users.find({}, {"password_hash": 0}))
    if not users:
        seed_default_user()
        users = list(db.users.find({}, {"password_hash": 0}))
    return [_serialize_doc(u) for u in users]


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    u = db.users.find_one({"id": user_id}, {"password_hash": 0})
    return _serialize_doc(u) if u else None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    u = db.users.find_one({"username": username.strip()})
    return _serialize_doc(u) if u else None


def get_user_by_login(username: str, email: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    u = db.users.find_one({
        "username": username.strip(),
        "email": email.strip().lower(),
    })
    return _serialize_doc(u) if u else None


def create_user(
    name: str,
    email: str,
    role: str = "operator",
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    db = get_db()
    clean_name = name.strip()
    clean_email = email.strip().lower()

    # Enforce exactly the authorized emails
    if clean_email not in settings.AUTHORIZED_EMAILS:
        raise ValueError(
            f"Registration rejected: Email '{clean_email}' is not in the list of authorized emails. "
            f"Permitted emails: {', '.join(settings.AUTHORIZED_EMAILS)}"
        )

    # Check if a user with this email already exists
    existing_email = db.users.find_one({"email": clean_email})
    if existing_email:
        raise ValueError(f"User with email '{clean_email}' already exists.")

    # Check maximum 3 users
    current_count = db.users.count_documents({})
    if current_count >= 3:
        raise ValueError("Registration rejected: Exactly 3 authorized users allowed, and all slots are filled.")

    uname = (username or clean_email.split("@")[0] or f"user_{current_count + 1}").strip()
    existing_uname = db.users.find_one({"username": uname})
    if existing_uname:
        uname = f"{uname}_{current_count + 1}"

    user_id = f"USR-{current_count + 1:03d}"
    pwd = password or "fisher2026"
    pwd_hash = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    doc = {
        "id": user_id,
        "username": uname,
        "name": clean_name,
        "email": clean_email,
        "role": role,
        "status": "active",
        "password_hash": pwd_hash,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    db.users.insert_one(doc)
    doc.pop("password_hash", None)
    logger.info(f"Created authorized user: {uname} ({clean_email})")
    return _serialize_doc(doc)


def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    db = get_db()
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    updates.pop("password_hash", None)

    # If updating email, check authorized list
    if "email" in updates:
        clean_email = updates["email"].strip().lower()
        if clean_email not in settings.AUTHORIZED_EMAILS:
            raise ValueError(f"Email '{clean_email}' is not authorized.")
        updates["email"] = clean_email

    res = db.users.find_one_and_update(
        {"id": user_id},
        {"$set": updates},
        projection={"password_hash": 0},
        return_document=True,
    )
    return _serialize_doc(res) if res else None


def delete_user(user_id: str) -> bool:
    db = get_db()
    result = db.users.delete_one({"id": user_id})
    return result.deleted_count > 0


def update_profile(user_id: str, name: Optional[str] = None, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
    updates: Dict[str, Any] = {}
    if name:
        updates["name"] = name.strip()
    if email:
        updates["email"] = email.strip().lower()
    return update_user(user_id, updates)


def update_password(user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    db = get_db()
    user = db.users.find_one({"id": user_id})
    if not user:
        return False, "User not found"

    curr_hash = user.get("password_hash", "")
    if curr_hash:
        try:
            if not bcrypt.checkpw(old_password.encode("utf-8"), curr_hash.encode("utf-8")):
                return False, "Incorrect current password"
        except Exception as e:
            logger.error(f"Error checking password: {e}")
            return False, "Authentication validation error"

    if len(new_password) < 6:
        return False, "New password must be at least 6 characters"

    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": new_hash, "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    return True, "Password updated successfully"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_session(user_id: str) -> str:
    db = get_db()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    db.sessions.insert_one({
        "token": token,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
    })
    return token


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    session = db.sessions.find_one({"token": token})
    if not session:
        return None
    user = db.users.find_one({"id": session["user_id"]}, {"password_hash": 0})
    return _serialize_doc(user) if user else None


def delete_session(token: str):
    db = get_db()
    db.sessions.delete_one({"token": token})


# ============================================================
# REPORTS WITH REAL DETECTION DATA & INTRUSION IMAGES
# ============================================================

def generate_report(title: str = "Detection Activity Report") -> Dict[str, Any]:
    """
    Generates a security documentation report containing REAL detection data,
    timestamps, camera info, alert details, intrusion image, and video reference.
    """
    db = get_db()
    detections = list(db.detections.find().sort("timestamp", DESCENDING).limit(100))
    count = db.reports.count_documents({})
    rep_id = f"REP-{count + 1:03d}"

    report_detections = []
    high_count = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for d in detections:
        item = _serialize_doc(d)
        if item.get("severity") in ["high", "critical"]:
            high_count += 1

        img = item.get("image")
        if not img and "description" in item:
            m = re.search(r"Image:\s*([^\s;]+)", item["description"])
            if m:
                img = m.group(1)
        if img:
            item["image"] = img
            item["imageUrl"] = f"/media/intrusions/{img}"

        vid = item.get("video")
        if not vid and "description" in item:
            m = re.search(r"Video:\s*([^\s;]+)", item["description"])
            if m:
                vid = m.group(1)
        if vid:
            item["video"] = vid
            item["videoUrl"] = f"/media/intrusions/{vid}"

        report_detections.append(item)

    summary = (
        f"This security report documents {len(report_detections)} AI-verified CCTV events. "
        f"{high_count} incidents are flagged as high/critical severity requiring review."
    )

    doc = {
        "id": rep_id,
        "title": title or "Detection Activity Report",
        "createdAt": now_str,
        "status": "ready",
        "totalDetections": len(report_detections),
        "highSeverityCount": high_count,
        "summary": summary,
        "detections": report_detections,
    }

    db.reports.update_one({"id": rep_id}, {"$set": doc}, upsert=True)
    logger.info(f"Generated report {rep_id} with {len(report_detections)} real detections.")
    return _serialize_doc(doc)


def get_reports(limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
    """Returns genuine reports from MongoDB without auto-generating dummy reports."""
    db = get_db()
    cursor = db.reports.find().sort("createdAt", DESCENDING).skip(skip).limit(limit)
    return [_serialize_doc(r) for r in cursor]


def get_report_by_id(rep_id: str) -> Optional[Dict[str, Any]]:
    db = get_db()
    doc = db.reports.find_one({"id": rep_id})
    return _serialize_doc(doc) if doc else None
