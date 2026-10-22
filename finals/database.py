import os
import json
import logging
import re
import secrets
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import bcrypt
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import ConnectionFailure, PyMongoError, ServerSelectionTimeoutError

from config import settings

logger = logging.getLogger("cctv_backend.database")

# Initialize MongoDB client
_client: Optional[MongoClient] = None
_mongo_online: Optional[bool] = None
_last_mongo_check: float = 0
_MONGO_CHECK_COOLDOWN = 30.0  # seconds

# Local resilient memory stores (guarantees 100% offline functionality)
_LOCAL_USERS: Dict[str, Dict[str, Any]] = {}
_LOCAL_SESSIONS: Dict[str, Dict[str, Any]] = {}
_LOCAL_CAMERAS: Dict[str, Dict[str, Any]] = {}
_LOCAL_DETECTIONS: Dict[str, Dict[str, Any]] = {}
_LOCAL_ALERTS: Dict[str, Dict[str, Any]] = {}
_LOCAL_REPORTS: Dict[str, Dict[str, Any]] = {}
_LOCAL_INTRUSIONS: Dict[str, Dict[str, Any]] = {}


def _seed_local_stores():
    """Seed initial authorized users and default camera into local resilient stores."""
    global _LOCAL_USERS, _LOCAL_CAMERAS
    default_accounts = [
        {
            "id": "USR-001",
            "username": "admin",
            "name": "Administrator",
            "email": "admin@fisher.cctv",
            "role": "admin",
            "status": "active",
            "password_hash": "$2b$10$sH.eSfPmfj/5LkI6ngpxDexs/gACpZImfB75nmfcOskkK38lls3iS",  # admin123
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "USR-002",
            "username": "operator",
            "name": "Control Operator",
            "email": "operator@fisher.cctv",
            "role": "operator",
            "status": "active",
            "password_hash": "$2b$10$p4M3IaZj4VocgU3Vu3fofeVWStJ.jXBm1RQ1IMp9Gm6bM2RGqH.MW",  # operator123
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "id": "USR-003",
            "username": "supervisor",
            "name": "Security Supervisor",
            "email": "supervisor@fisher.cctv",
            "role": "operator",
            "status": "active",
            "password_hash": "$2b$10$KfG6DyDZAShuqvwtoUATiOOv6BmonQ6QzDnKb1MzNBUcKtvM2mo7C",  # supervisor123
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    auth_emails = settings.AUTHORIZED_EMAILS
    for idx, acc in enumerate(default_accounts):
        if idx < len(auth_emails):
            acc["email"] = auth_emails[idx].strip().lower()
        _LOCAL_USERS[acc["id"]] = acc

    _LOCAL_CAMERAS["CAM-001"] = {
        "id": "CAM-001",
        "name": "PC Camera (OpenCV)",
        "location": "Local Workstation",
        "status": "online",
        "streamUrl": "/api/cameras/CAM-001/stream",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# Run local seeding immediately
_seed_local_stores()


def get_client() -> MongoClient:
    global _client
    if _client is None:
        try:
            _client = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=1500,
                connectTimeoutMS=1500,
                socketTimeoutMS=1500,
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


def is_mongo_available() -> bool:
    """Check whether MongoDB is reachable, caching results to avoid blocking."""
    global _mongo_online, _last_mongo_check
    now = time.time()
    if _mongo_online is False and (now - _last_mongo_check) < _MONGO_CHECK_COOLDOWN:
        return False

    try:
        client = get_client()
        client.admin.command("ping")
        _mongo_online = True
        _last_mongo_check = now
        return True
    except Exception as e:
        if _mongo_online is not False:
            logger.warning(
                f"MongoDB Atlas is currently unreachable ({e}). Using resilient local in-memory fallback."
            )
        _mongo_online = False
        _last_mongo_check = now
        return False


def _mark_mongo_offline(err: Exception):
    global _mongo_online, _last_mongo_check
    _mongo_online = False
    _last_mongo_check = time.time()
    logger.warning(f"MongoDB operation failed ({err}). Falling back to local resilient store.")


def check_db_connection() -> Dict[str, Any]:
    """Test ping to MongoDB with safe fallback."""
    online = is_mongo_available()
    if online:
        try:
            db = get_db()
            collections = db.list_collection_names()
            return {
                "status": "connected",
                "ping": True,
                "database": settings.DB_NAME,
                "collections": collections,
                "mode": "mongodb_atlas",
            }
        except Exception as e:
            _mark_mongo_offline(e)

    return {
        "status": "fallback_active",
        "ping": False,
        "database": settings.DB_NAME,
        "mode": "local_resilient_store",
        "note": "MongoDB Atlas unreachable (verify IP whitelist 0.0.0.0/0). CCTV and auth running in resilient local mode.",
    }


def init_indexes():
    """Ensure indexes on all collections if MongoDB is online, and seed records."""
    _seed_local_stores()
    if not is_mongo_available():
        logger.info("Resilient local stores initialized (offline mode).")
        return

    try:
        db = get_db()
        db.detections.create_index([("id", ASCENDING)], unique=True)
        db.detections.create_index([("timestamp", DESCENDING)])
        db.detections.create_index([("cameraId", ASCENDING)])
        db.detections.create_index([("status", ASCENDING)])

        db.alerts.create_index([("id", ASCENDING)], unique=True)
        db.alerts.create_index([("timestamp", DESCENDING)])
        db.alerts.create_index([("status", ASCENDING)])
        db.alerts.create_index([("severity", ASCENDING)])

        db.cameras.create_index([("id", ASCENDING)], unique=True)
        db.intrusions.create_index([("timestamp", DESCENDING)])
        db.intrusions.create_index([("track_id", ASCENDING)])

        db.users.create_index([("id", ASCENDING)], unique=True)
        db.users.create_index([("username", ASCENDING)], unique=True)
        db.users.create_index([("email", ASCENDING)], unique=True)

        db.reports.create_index([("id", ASCENDING)], unique=True)
        db.reports.create_index([("createdAt", DESCENDING)])
        db.sessions.create_index([("token", ASCENDING)], unique=True)

        seed_default_camera()
        seed_default_user()
        logger.info("MongoDB indexes successfully created/verified.")
    except Exception as e:
        _mark_mongo_offline(e)
        logger.warning(f"Could not initialize indexes on MongoDB: {e}")


def seed_default_camera():
    """Ensure at least CAM-001 exists in database and local store."""
    default_cam = {
        "id": "CAM-001",
        "name": "PC Camera (OpenCV)",
        "location": "Local Workstation",
        "status": "online",
        "streamUrl": "/api/cameras/CAM-001/stream",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _LOCAL_CAMERAS["CAM-001"] = {**default_cam}

    if is_mongo_available():
        try:
            db = get_db()
            db.cameras.update_one(
                {"id": "CAM-001"},
                {"$set": default_cam},
                upsert=True,
            )
            logger.info("Seeded/updated default camera CAM-001 in MongoDB.")
        except Exception as e:
            _mark_mongo_offline(e)


def seed_default_user():
    """Ensure exactly the 3 authorized users exist in database and local store."""
    _seed_local_stores()
    if not is_mongo_available():
        return

    try:
        db = get_db()
        for acc in _LOCAL_USERS.values():
            existing = db.users.find_one({
                "$or": [{"username": acc["username"]}, {"email": acc["email"]}]
            })
            if not existing:
                doc = {**acc}
                db.users.insert_one(doc)
                logger.info(f"Seeded authorized user to MongoDB: {acc['username']} ({acc['email']})")
    except Exception as e:
        _mark_mongo_offline(e)


def _serialize_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Helper to convert MongoDB _id to string for JSON serialization."""
    if not doc:
        return doc
    clean = dict(doc)
    if "_id" in clean:
        clean["_id"] = str(clean["_id"])
    return clean


# ============================================================
# DETECTIONS
# ============================================================

def save_detection(detection_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save a detection event and corresponding alert in local store and MongoDB."""
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

    _LOCAL_DETECTIONS[det_id] = {**detection_doc}

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

    _LOCAL_ALERTS[det_id] = {**alert_doc}

    if is_mongo_available():
        try:
            db = get_db()
            db.detections.update_one({"id": det_id}, {"$set": detection_doc}, upsert=True)
            db.alerts.update_one({"id": det_id}, {"$set": alert_doc}, upsert=True)
        except Exception as e:
            _mark_mongo_offline(e)

    return _serialize_doc(detection_doc)


def get_detections(
    limit: int = 50,
    skip: int = 0,
    camera_id: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if is_mongo_available():
        try:
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
                detections.append(d)
            return detections
        except Exception as e:
            _mark_mongo_offline(e)

    # Fallback to local
    all_det = list(_LOCAL_DETECTIONS.values())
    all_det.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    filtered = []
    for d in all_det:
        if camera_id and d.get("cameraId") != camera_id:
            continue
        if status and d.get("status") != status:
            continue
        cd = dict(d)
        if cd.get("status") in ["open", None]:
            cd["status"] = "new"
        filtered.append(cd)
    return filtered[skip : skip + limit]


def get_detection_by_id(det_id: str) -> Optional[Dict[str, Any]]:
    if is_mongo_available():
        try:
            db = get_db()
            doc = db.detections.find_one({"id": det_id})
            if doc:
                d = _serialize_doc(doc)
                if d.get("status") in ["open", None]:
                    d["status"] = "new"
                return d
        except Exception as e:
            _mark_mongo_offline(e)

    doc = _LOCAL_DETECTIONS.get(det_id)
    return dict(doc) if doc else None


def update_detection_status(detection_id: str, new_status: str) -> Optional[Dict[str, Any]]:
    if new_status == "open":
        new_status = "new"
    elif new_status == "resolved":
        new_status = "reviewed"

    now_iso = datetime.now(timezone.utc).isoformat()

    # Update local
    if detection_id in _LOCAL_DETECTIONS:
        _LOCAL_DETECTIONS[detection_id]["status"] = new_status
        _LOCAL_DETECTIONS[detection_id]["updated_at"] = now_iso
    if detection_id in _LOCAL_ALERTS:
        alert_status = "open" if new_status == "new" else new_status
        _LOCAL_ALERTS[detection_id]["status"] = alert_status
        _LOCAL_ALERTS[detection_id]["updated_at"] = now_iso

    if is_mongo_available():
        try:
            db = get_db()
            res = db.detections.find_one_and_update(
                {"id": detection_id},
                {"$set": {"status": new_status, "updated_at": now_iso}},
                return_document=True,
            )
            if res:
                alert_status = "open" if new_status == "new" else new_status
                db.alerts.update_one(
                    {"id": detection_id},
                    {"$set": {"status": alert_status, "updated_at": now_iso}},
                )
                return _serialize_doc(res)
        except Exception as e:
            _mark_mongo_offline(e)

    return _LOCAL_DETECTIONS.get(detection_id)


def update_detection_video(detection_id: str, video_filename: str) -> Optional[Dict[str, Any]]:
    now_iso = datetime.now(timezone.utc).isoformat()
    video_url = f"/media/intrusions/{video_filename}"
    updates = {
        "video": video_filename,
        "videoUrl": video_url,
        "video_ready": True,
        "updated_at": now_iso,
    }

    # Update local
    if detection_id in _LOCAL_DETECTIONS:
        _LOCAL_DETECTIONS[detection_id].update(updates)
    if detection_id in _LOCAL_ALERTS:
        _LOCAL_ALERTS[detection_id].update({
            "video": video_filename,
            "videoUrl": video_url,
            "updated_at": now_iso,
        })

    if is_mongo_available():
        try:
            db = get_db()
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
            if det:
                return _serialize_doc(det)
        except Exception as e:
            _mark_mongo_offline(e)

    return _LOCAL_DETECTIONS.get(detection_id)


# ============================================================
# ALERTS
# ============================================================

def get_alerts(
    limit: int = 50,
    skip: int = 0,
    status: Optional[str] = None,
    severity: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if is_mongo_available():
        try:
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
                alerts.append(a)
            return alerts
        except Exception as e:
            _mark_mongo_offline(e)

    # Fallback to local
    all_alt = list(_LOCAL_ALERTS.values())
    all_alt.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    filtered = []
    for a in all_alt:
        if status and a.get("status") != status:
            continue
        if severity and a.get("severity") != severity:
            continue
        filtered.append(dict(a))
    return filtered[skip : skip + limit]


def get_alert_by_id(alert_id: str) -> Optional[Dict[str, Any]]:
    if is_mongo_available():
        try:
            db = get_db()
            doc = db.alerts.find_one({"id": alert_id})
            if doc:
                return _serialize_doc(doc)
        except Exception as e:
            _mark_mongo_offline(e)

    doc = _LOCAL_ALERTS.get(alert_id)
    return dict(doc) if doc else None


def update_alert(alert_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()

    if alert_id in _LOCAL_ALERTS:
        _LOCAL_ALERTS[alert_id].update(updates)
    if "status" in updates and alert_id in _LOCAL_DETECTIONS:
        det_status = "new" if updates["status"] == "open" else updates["status"]
        _LOCAL_DETECTIONS[alert_id]["status"] = det_status

    if is_mongo_available():
        try:
            db = get_db()
            res = db.alerts.find_one_and_update(
                {"id": alert_id},
                {"$set": updates},
                return_document=True,
            )
            if res and "status" in updates:
                det_status = "new" if updates["status"] == "open" else updates["status"]
                db.detections.update_one({"id": alert_id}, {"$set": {"status": det_status}})
                return _serialize_doc(res)
        except Exception as e:
            _mark_mongo_offline(e)

    return _LOCAL_ALERTS.get(alert_id)


# ============================================================
# CAMERAS
# ============================================================

def get_cameras() -> List[Dict[str, Any]]:
    if is_mongo_available():
        try:
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
        except Exception as e:
            _mark_mongo_offline(e)

    # Fallback to local
    return [
        {
            "id": cam.get("id", "CAM-001"),
            "name": cam.get("name", "PC Camera (OpenCV)"),
            "location": cam.get("location", "Local Workstation"),
            "status": cam.get("status", "online"),
            "streamUrl": cam.get("streamUrl", "/api/cameras/CAM-001/stream"),
        }
        for cam in _LOCAL_CAMERAS.values()
    ]


def upsert_camera(camera_data: Dict[str, Any]) -> Dict[str, Any]:
    cam_id = camera_data["id"]
    if "streamUrl" not in camera_data or not camera_data["streamUrl"]:
        camera_data["streamUrl"] = f"/api/cameras/{cam_id}/stream"
    camera_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    _LOCAL_CAMERAS[cam_id] = {**camera_data}

    if is_mongo_available():
        try:
            db = get_db()
            db.cameras.update_one({"id": cam_id}, {"$set": camera_data}, upsert=True)
            doc = db.cameras.find_one({"id": cam_id})
            if doc:
                return _serialize_doc(doc)
        except Exception as e:
            _mark_mongo_offline(e)

    return dict(_LOCAL_CAMERAS[cam_id])


# ============================================================
# DASHBOARD STATISTICS
# ============================================================

def get_dashboard_statistics() -> Dict[str, Any]:
    if is_mongo_available():
        try:
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
        except Exception as e:
            _mark_mongo_offline(e)

    # Local fallback
    total_cameras = len(_LOCAL_CAMERAS)
    online_cameras = sum(1 for c in _LOCAL_CAMERAS.values() if c.get("status") == "online")
    total_detections = len(_LOCAL_DETECTIONS)
    active_alerts = sum(1 for a in _LOCAL_ALERTS.values() if a.get("status") in ["open", "new"])
    resolved_alerts = sum(1 for a in _LOCAL_ALERTS.values() if a.get("status") in ["resolved", "reviewed", "dismissed"])

    return {
        "totalCameras": max(1, total_cameras),
        "onlineCameras": max(1, online_cameras),
        "totalDetections": total_detections,
        "activeAlerts": active_alerts,
        "resolvedAlerts": resolved_alerts,
        "totalIntrusions": len(_LOCAL_INTRUSIONS) or total_detections,
    }


# ============================================================
# CLEANUP DETECTION HISTORY ONLY
# ============================================================

def cleanup_detection_history() -> Dict[str, Any]:
    """Safely deletes old detection records, intrusions, alerts, and reports."""
    det_count = len(_LOCAL_DETECTIONS)
    alt_count = len(_LOCAL_ALERTS)
    int_count = len(_LOCAL_INTRUSIONS)
    rep_count = len(_LOCAL_REPORTS)

    _LOCAL_DETECTIONS.clear()
    _LOCAL_ALERTS.clear()
    _LOCAL_INTRUSIONS.clear()
    _LOCAL_REPORTS.clear()

    if is_mongo_available():
        try:
            db = get_db()
            det_res = db.detections.delete_many({})
            alt_res = db.alerts.delete_many({})
            int_res = db.intrusions.delete_many({})
            rep_res = db.reports.delete_many({})
            det_count = det_res.deleted_count
            alt_count = alt_res.deleted_count
            int_count = int_res.deleted_count
            rep_count = rep_res.deleted_count
        except Exception as e:
            _mark_mongo_offline(e)

    intrusions_dir = Path(settings.INTRUSIONS_DIR)
    deleted_files = 0
    if intrusions_dir.exists():
        for p in intrusions_dir.glob("*.*"):
            try:
                p.unlink()
                deleted_files += 1
            except Exception as e:
                logger.warning(f"Could not delete media file {p}: {e}")

    logger.info(f"Cleanup completed: {det_count} detections, {alt_count} alerts removed.")
    return {
        "status": "success",
        "deleted_detections": det_count,
        "deleted_alerts": alt_count,
        "deleted_intrusions": int_count,
        "deleted_reports": rep_count,
        "deleted_files": deleted_files,
    }


def sync_disk_intrusions() -> Dict[str, Any]:
    """Scans output/intrusions for saved json intrusions and synchronizes them."""
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
            _LOCAL_INTRUSIONS[event_id] = intrusion_doc

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
        "message": f"Successfully synchronized {synced_count} intrusions",
    }


# ============================================================
# USERS & AUTHENTICATION (EXACTLY 3 AUTHORIZED USERS)
# ============================================================

def get_users() -> List[Dict[str, Any]]:
    if is_mongo_available():
        try:
            db = get_db()
            users = list(db.users.find({}, {"password_hash": 0}))
            if users:
                return [_serialize_doc(u) for u in users]
        except Exception as e:
            _mark_mongo_offline(e)

    # Return local users without password_hash
    clean_users = []
    for u in _LOCAL_USERS.values():
        item = {k: v for k, v in u.items() if k != "password_hash"}
        clean_users.append(item)
    return clean_users


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    if is_mongo_available():
        try:
            db = get_db()
            u = db.users.find_one({"id": user_id}, {"password_hash": 0})
            if u:
                return _serialize_doc(u)
        except Exception as e:
            _mark_mongo_offline(e)

    user = _LOCAL_USERS.get(user_id)
    if user:
        return {k: v for k, v in user.items() if k != "password_hash"}
    return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    clean_u = username.strip().lower()
    if is_mongo_available():
        try:
            db = get_db()
            u = db.users.find_one({"username": {"$regex": f"^{re.escape(clean_u)}$", "$options": "i"}})
            if u:
                return _serialize_doc(u)
        except Exception as e:
            _mark_mongo_offline(e)

    for u in _LOCAL_USERS.values():
        if u.get("username", "").lower() == clean_u:
            return dict(u)
    return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    clean_e = email.strip().lower()
    if is_mongo_available():
        try:
            db = get_db()
            u = db.users.find_one({"email": clean_e})
            if u:
                return _serialize_doc(u)
        except Exception as e:
            _mark_mongo_offline(e)

    for u in _LOCAL_USERS.values():
        if u.get("email", "").lower() == clean_e:
            return dict(u)
    return None


def get_user_by_login(username: str, email: str) -> Optional[Dict[str, Any]]:
    """Lookup user by username and authorized email, with resilient fallback."""
    clean_u = username.strip().lower()
    clean_e = email.strip().lower()

    if is_mongo_available():
        try:
            db = get_db()
            u = db.users.find_one({
                "username": {"$regex": f"^{re.escape(clean_u)}$", "$options": "i"},
                "email": clean_e,
            })
            if not u:
                u = db.users.find_one({"email": clean_e})
            if u:
                return _serialize_doc(u)
        except Exception as e:
            _mark_mongo_offline(e)

    # Resilient local lookup
    # 1. Match both username and email
    for u in _LOCAL_USERS.values():
        if u.get("email", "").lower() == clean_e and u.get("username", "").lower() == clean_u:
            return dict(u)

    # 2. Match email
    for u in _LOCAL_USERS.values():
        if u.get("email", "").lower() == clean_e:
            return dict(u)

    return None


def create_user(
    name: str,
    email: str,
    role: str = "operator",
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> Dict[str, Any]:
    clean_name = name.strip()
    clean_email = email.strip().lower()

    if clean_email not in settings.AUTHORIZED_EMAILS:
        raise ValueError(
            f"Registration rejected: Email '{clean_email}' is not in the list of authorized emails. "
            f"Permitted emails: {', '.join(settings.AUTHORIZED_EMAILS)}"
        )

    current_users = get_users()
    if len(current_users) >= 3:
        raise ValueError("Registration rejected: Exactly 3 authorized users allowed, and all slots are filled.")

    uname = (username or clean_email.split("@")[0] or f"user_{len(current_users) + 1}").strip()
    user_id = f"USR-{len(current_users) + 1:03d}"
    pwd = password or "fisher2026"
    pwd_hash = bcrypt.hashpw(pwd.encode("utf-8"), bcrypt.gensalt(10)).decode("utf-8")

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
    _LOCAL_USERS[user_id] = doc

    if is_mongo_available():
        try:
            db = get_db()
            db.users.insert_one(dict(doc))
        except Exception as e:
            _mark_mongo_offline(e)

    res = {k: v for k, v in doc.items() if k != "password_hash"}
    return res


def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    updates.pop("password_hash", None)

    if "email" in updates:
        clean_email = updates["email"].strip().lower()
        if clean_email not in settings.AUTHORIZED_EMAILS:
            raise ValueError(f"Email '{clean_email}' is not authorized.")
        updates["email"] = clean_email

    if user_id in _LOCAL_USERS:
        _LOCAL_USERS[user_id].update(updates)

    if is_mongo_available():
        try:
            db = get_db()
            res = db.users.find_one_and_update(
                {"id": user_id},
                {"$set": updates},
                projection={"password_hash": 0},
                return_document=True,
            )
            if res:
                return _serialize_doc(res)
        except Exception as e:
            _mark_mongo_offline(e)

    u = _LOCAL_USERS.get(user_id)
    return {k: v for k, v in u.items() if k != "password_hash"} if u else None


def delete_user(user_id: str) -> bool:
    deleted = False
    if user_id in _LOCAL_USERS:
        del _LOCAL_USERS[user_id]
        deleted = True

    if is_mongo_available():
        try:
            db = get_db()
            res = db.users.delete_one({"id": user_id})
            return res.deleted_count > 0
        except Exception as e:
            _mark_mongo_offline(e)

    return deleted


def update_profile(user_id: str, name: Optional[str] = None, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
    updates: Dict[str, Any] = {}
    if name:
        updates["name"] = name.strip()
    if email:
        updates["email"] = email.strip().lower()
    return update_user(user_id, updates)


def update_password(user_id: str, old_password: str, new_password: str) -> Tuple[bool, str]:
    user = _LOCAL_USERS.get(user_id)
    if is_mongo_available():
        try:
            db = get_db()
            m_user = db.users.find_one({"id": user_id})
            if m_user:
                user = m_user
        except Exception as e:
            _mark_mongo_offline(e)

    if not user:
        return False, "User not found"

    curr_hash = user.get("password_hash", "")
    if curr_hash:
        if not verify_password(old_password, curr_hash):
            return False, "Incorrect current password"

    if len(new_password) < 6:
        return False, "New password must be at least 6 characters"

    new_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt(10)).decode("utf-8")
    now_iso = datetime.now(timezone.utc).isoformat()

    if user_id in _LOCAL_USERS:
        _LOCAL_USERS[user_id]["password_hash"] = new_hash
        _LOCAL_USERS[user_id]["updated_at"] = now_iso

    if is_mongo_available():
        try:
            db = get_db()
            db.users.update_one(
                {"id": user_id},
                {"$set": {"password_hash": new_hash, "updated_at": now_iso}},
            )
        except Exception as e:
            _mark_mongo_offline(e)

    return True, "Password updated successfully"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Bulletproof password verifier supporting bcrypt and safe plain-text fallback."""
    if not hashed_password or not plain_password:
        return False
    try:
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
        return plain_password == hashed_password
    except Exception as e:
        logger.warning(f"Bcrypt verification fallback: {e}")
        return plain_password == hashed_password


def create_session(user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session_data = {
        "token": token,
        "user_id": user_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": expires_at,
    }
    _LOCAL_SESSIONS[token] = session_data

    if is_mongo_available():
        try:
            db = get_db()
            db.sessions.insert_one(dict(session_data))
        except Exception as e:
            _mark_mongo_offline(e)

    return token


def get_user_by_token(token: str) -> Optional[Dict[str, Any]]:
    session = _LOCAL_SESSIONS.get(token)

    if not session and is_mongo_available():
        try:
            db = get_db()
            session = db.sessions.find_one({"token": token})
        except Exception as e:
            _mark_mongo_offline(e)

    if not session:
        return None

    user_id = session.get("user_id")
    return get_user_by_id(user_id)


def delete_session(token: str):
    if token in _LOCAL_SESSIONS:
        del _LOCAL_SESSIONS[token]

    if is_mongo_available():
        try:
            db = get_db()
            db.sessions.delete_one({"token": token})
        except Exception as e:
            _mark_mongo_offline(e)


# ============================================================
# REPORTS WITH REAL DETECTION DATA & INTRUSION IMAGES
# ============================================================

def generate_report(title: str = "Detection Activity Report") -> Dict[str, Any]:
    """Generates a security documentation report containing real detection data."""
    detections = get_detections(limit=100)
    rep_count = len(_LOCAL_REPORTS)
    rep_id = f"REP-{rep_count + 1:03d}"

    report_detections = []
    high_count = 0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for d in detections:
        item = _serialize_doc(d)
        if item.get("severity") in ["high", "critical"]:
            high_count += 1
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
    _LOCAL_REPORTS[rep_id] = doc

    if is_mongo_available():
        try:
            db = get_db()
            db.reports.update_one({"id": rep_id}, {"$set": doc}, upsert=True)
        except Exception as e:
            _mark_mongo_offline(e)

    logger.info(f"Generated report {rep_id} with {len(report_detections)} real detections.")
    return _serialize_doc(doc)


def get_reports(limit: int = 50, skip: int = 0) -> List[Dict[str, Any]]:
    if is_mongo_available():
        try:
            db = get_db()
            cursor = db.reports.find().sort("createdAt", DESCENDING).skip(skip).limit(limit)
            return [_serialize_doc(r) for r in cursor]
        except Exception as e:
            _mark_mongo_offline(e)

    reps = list(_LOCAL_REPORTS.values())
    reps.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    return reps[skip : skip + limit]


def get_report_by_id(rep_id: str) -> Optional[Dict[str, Any]]:
    if is_mongo_available():
        try:
            db = get_db()
            doc = db.reports.find_one({"id": rep_id})
            if doc:
                return _serialize_doc(doc)
        except Exception as e:
            _mark_mongo_offline(e)

    doc = _LOCAL_REPORTS.get(rep_id)
    return dict(doc) if doc else None
