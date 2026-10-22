import cv2
import time
import signal
import sys
import os
import json
import requests
import threading
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from config import settings
from yolo_detector import ObjectDetector
from analysis import ActivityDetector
from alert_system import AlertSystem

# ============================================================
# CONFIGURATION
# ============================================================

# 0 = Physical PC Camera (will use backend raw-stream if backend is running to avoid hardware conflict)
VIDEO_SOURCE = 0

# Internal frame size
RESIZE = (1280, 720)

# Display desktop window? Set to False so feed displays inside dashboard, not in separate desktop window
SHOW_PREVIEW = False

# YOLO & Tracker
CONFIDENCE = 0.5
MODEL_PATH = "yolov8n.pt"
TRACKER_CONFIG = "custom_botsort.yaml"

# Restricted Area Box (Center)
RESTRICTED_AREA_WIDTH = 400
RESTRICTED_AREA_HEIGHT = 600

# Intrusion Video Duration (Exactly 2 minutes = 120 seconds)
INTRUSION_VIDEO_SECONDS = settings.INTRUSION_VIDEO_SECONDS  # 120s
VIDEO_CODEC = "mp4v"

# Tracking Protection
TRACK_LOST_GRACE_FRAMES = 90

# Output directories
OUTPUT_DIR = str(settings.OUTPUT_DIR)
INTRUSION_DIR = str(settings.INTRUSIONS_DIR)
os.makedirs(INTRUSION_DIR, exist_ok=True)

# API Endpoints
BACKEND_STREAM_URL = f"{settings.API_BASE_URL}/api/cameras/CAM-001/raw-stream"
BACKEND_LIVE_FRAME_URL = f"{settings.API_BASE_URL}/api/cameras/CAM-001/live-frame"
API_DETECTIONS_URL = settings.API_DETECTIONS_URL

# ============================================================
# CONTROL & GRACEFUL SHUTDOWN
# ============================================================

running = True


def stop_program(signum=None, frame=None):
    global running
    print("\n[INFO] Graceful shutdown initiated (Ctrl+C). Cleaning up resources...")
    running = False


signal.signal(signal.SIGINT, stop_program)
signal.signal(signal.SIGTERM, stop_program)


# ============================================================
# RESTRICTED AREA HELPERS
# ============================================================

def get_restricted_area(frame_width, frame_height):
    area_width = min(RESTRICTED_AREA_WIDTH, frame_width)
    area_height = min(RESTRICTED_AREA_HEIGHT, frame_height)
    x1 = int((frame_width - area_width) / 2)
    y1 = int((frame_height - area_height) / 2)
    x2 = x1 + area_width
    y2 = y1 + area_height
    return (x1, y1, x2, y2)


def is_person_inside_restricted_area(bbox, restricted_area):
    x1, y1, x2, y2 = bbox
    area_x1, area_y1, area_x2, area_y2 = restricted_area
    center_x = int((x1 + x2) / 2)
    center_y = int((y1 + y2) / 2)
    return area_x1 <= center_x <= area_x2 and area_y1 <= center_y <= area_y2


def get_bbox_center(bbox):
    x1, y1, x2, y2 = bbox
    return int((x1 + x2) / 2), int((y1 + y2) / 2)


def determine_activity(current_center, previous_center):
    if previous_center is None:
        return "entering_restricted_area"
    current_x, current_y = current_center
    previous_x, previous_y = previous_center
    movement = abs(current_x - previous_x) + abs(current_y - previous_y)
    return "stationary_inside_restricted_area" if movement < 8 else "moving_inside_restricted_area"


# ============================================================
# CREATE INTRUSION EVENT
# ============================================================

def create_intrusion_event(frame, track_id, confidence, activity):
    now = datetime.now()
    timestamp_for_filename = now.strftime("%Y%m%d_%H%M%S")
    timestamp_for_json = now.strftime("%Y-%m-%d %H:%M:%S")

    event_name = f"intrusion_{timestamp_for_filename}_ID{track_id}"
    image_filename = f"{event_name}_1.jpg"
    image_path = os.path.join(INTRUSION_DIR, image_filename)

    video_filename = f"{event_name}.mp4"
    video_path = os.path.join(INTRUSION_DIR, video_filename)

    json_filename = f"{event_name}.json"
    json_path = os.path.join(INTRUSION_DIR, json_filename)

    # Save first frame (Frame 1)
    success = cv2.imwrite(image_path, frame)
    if not success:
        print(f"[ERROR] Could not save intrusion frame: {image_path}")
        return None

    event_data = {
        "event": "restricted_area_intrusion",
        "track_id": int(track_id),
        "object": "person",
        "confidence": round(float(confidence), 3),
        "activity": activity,
        "message": "Person entered the restricted area.",
        "image": image_filename,
        "video": video_filename,
        "video_duration_seconds": INTRUSION_VIDEO_SECONDS,
        "timestamp": timestamp_for_json,
    }

    try:
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(event_data, json_file, indent=4)
    except Exception as error:
        print(f"[ERROR] Could not save intrusion JSON: {error}")
        return None

    det_id = f"DET-{timestamp_for_json}-{track_id}".replace(" ", "T").replace(":", "-")
    event_data["id"] = det_id

    print("\n" + "=" * 65)
    print(f"[INTRUSION ALERT CONFIRMED] ID={track_id} at {timestamp_for_json}")
    print(f"Confidence : {confidence:.3f}")
    print(f"Activity   : {activity}")
    print(f"Frame 1    : {image_path}")
    print(f"Video Path : {video_path} (Recording {INTRUSION_VIDEO_SECONDS}s)")
    print("=" * 65 + "\n")

    return {
        "event_data": event_data,
        "det_id": det_id,
        "image_path": image_path,
        "video_path": video_path,
        "json_path": json_path,
        "video_filename": video_filename,
    }


def update_event_json(json_path, event_data, video_ready):
    event_data["video_ready"] = bool(video_ready)
    try:
        with open(json_path, "w", encoding="utf-8") as json_file:
            json.dump(event_data, json_file, indent=4)
    except Exception as error:
        print(f"[ERROR] Could not update event JSON: {error}")


# ============================================================
# DASHBOARD API SYNCHRONIZATION
# ============================================================

def send_detection_to_dashboard(event_data):
    """Sends initial intrusion alert with image snapshot to dashboard asynchronously."""
    det_id = event_data.get("id")
    conf = event_data.get("confidence", 0.95)
    conf_pct = round(conf * 100, 2) if conf <= 1.0 else round(conf, 2)
    image_name = event_data.get("image")
    image_url = f"/media/intrusions/{image_name}" if image_name else None

    payload = {
        "id": det_id,
        "cameraId": "CAM-001",
        "type": event_data.get("message", "Person entered the restricted area."),
        "confidence": conf_pct,
        "severity": "high",
        "timestamp": event_data["timestamp"],
        "status": "new",
        "image": image_name,
        "imageUrl": image_url,
        "video": None,
        "videoUrl": None,
        "description": (
            f"Object: {event_data.get('object', 'person')}; "
            f"Activity: {event_data.get('activity', 'intrusion')}; "
            f"Track ID: {event_data.get('track_id')}; "
            f"Image: {image_name or 'snapshot'}"
        ),
    }

    def _worker():
        try:
            res = requests.post(API_DETECTIONS_URL, json=payload, timeout=3)
            res.raise_for_status()
            print(f"[API] Initial detection alert sent to dashboard (ID: {det_id}).")
        except Exception as err:
            logger_err = str(err)
            print(f"[API] Dashboard detection sync note: {logger_err}")

    threading.Thread(target=_worker, daemon=True).start()


def send_video_to_dashboard(det_id: str, video_filename: str):
    """Sends the completed 2-minute video recording to the dashboard."""
    video_endpoint = f"{API_DETECTIONS_URL}/{det_id}/video"
    video_url = f"/media/intrusions/{video_filename}"
    payload = {
        "video": video_filename,
        "videoUrl": video_url,
        "video_ready": True,
    }

    def _worker():
        try:
            res = requests.post(video_endpoint, json=payload, timeout=4)
            res.raise_for_status()
            print(f"[API] Completed 2-minute video sent to dashboard (ID: {det_id}).")
        except Exception:
            try:
                requests.patch(video_endpoint, json=payload, timeout=4)
            except Exception as e2:
                print(f"[API ERROR] Failed sending video to dashboard: {e2}")

    threading.Thread(target=_worker, daemon=True).start()


# Feed live frame to dashboard
def push_frame_to_dashboard(frame_bytes):
    def _post():
        try:
            requests.post(
                BACKEND_LIVE_FRAME_URL,
                data=frame_bytes,
                headers={"Content-Type": "image/jpeg"},
                timeout=0.5,
            )
        except Exception:
            pass

    threading.Thread(target=_post, daemon=True).start()


# ============================================================
# INITIALIZE DETECTION ENGINES
# ============================================================

print("=" * 65)
print("FISHER AI CCTV — INTRUSION DETECTION SYSTEM")
print("=" * 65)
print(f"[INFO] Video Source        : {VIDEO_SOURCE}")
print(f"[INFO] Model               : {MODEL_PATH}")
print(f"[INFO] Confidence          : {CONFIDENCE}")
print(f"[INFO] Video Duration      : {INTRUSION_VIDEO_SECONDS}s (2 Minutes)")
print(f"[INFO] Restricted Area     : {RESTRICTED_AREA_WIDTH} x {RESTRICTED_AREA_HEIGHT}")
print(f"[INFO] Backend API URL     : {settings.API_BASE_URL}")

detector = ObjectDetector(
    confidence=CONFIDENCE,
    model_path=MODEL_PATH,
    tracker_config=TRACKER_CONFIG,
)
activity_detector = ActivityDetector()
alert_system = AlertSystem(
    bot_token=settings.BOT_TOKEN,
    chat_id=settings.CHAT_ID,
    async_mode=True,
)

# ============================================================
# OPEN VIDEO SOURCE (AVOID HARDWARE DEVICE CONFLICT)
# ============================================================

cap = None

# 1. If backend server is running, consume its raw camera stream to prevent hardware conflict
if VIDEO_SOURCE == 0:
    try:
        test_res = requests.get(f"{settings.API_BASE_URL}/health", timeout=1.0)
        if test_res.ok:
            print("[INFO] Unified Backend service detected. Connecting to backend raw camera stream...")
            cap = cv2.VideoCapture(BACKEND_STREAM_URL)
            if cap.isOpened():
                print("[INFO] Successfully connected to backend raw camera stream.")
    except Exception:
        pass

# 2. If stream not opened, open physical camera directly
if cap is None or not cap.isOpened():
    print("[INFO] Opening physical PC camera directly...")
    cap = cv2.VideoCapture(VIDEO_SOURCE, cv2.CAP_DSHOW) if isinstance(VIDEO_SOURCE, int) else cv2.VideoCapture(VIDEO_SOURCE)
    if not cap.isOpened():
        cap = cv2.VideoCapture(VIDEO_SOURCE)

if not cap.isOpened():
    print("[ERROR] Could not open camera video source. Ensure camera is connected.")
    detector.close()
    sys.exit(1)

source_fps = cap.get(cv2.CAP_PROP_FPS)
if source_fps <= 0 or source_fps > 120:
    source_fps = 30.0

print(f"[INFO] Camera stream active (FPS: {source_fps:.1f}). Ready for intrusion monitoring.")

# State tracking
alerted_ids = set()
alert_cooldowns = {}
GLOBAL_ALERT_COOLDOWN = 15.0
last_global_alert_time = 0.0

missing_frames = {}
previous_centers = {}
active_recordings = {}

frame_count = 0
last_push_time = 0.0

try:
    while running:
        ret, frame = cap.read()
        if not ret or frame is None:
            time.sleep(0.04)
            continue

        frame_count += 1

        if RESIZE is not None:
            frame = cv2.resize(frame, RESIZE)

        frame_height, frame_width = frame.shape[:2]
        restricted_area = get_restricted_area(frame_width, frame_height)

        # Run YOLO + BoT-SORT
        processed_frame = detector.process_frame(frame.copy(), draw=True)
        current_tracks = detector.get_tracks()
        current_visible_ids = set(current_tracks.keys())

        # Draw Restricted Area Box
        area_x1, area_y1, area_x2, area_y2 = restricted_area
        cv2.rectangle(
            processed_frame,
            (area_x1, area_y1),
            (area_x2, area_y2),
            (0, 0, 255),
            3,
        )
        cv2.putText(
            processed_frame,
            "RESTRICTED AREA",
            (area_x1, max(area_y1 - 10, 25)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2,
        )

        now_sec = time.time()

        # Check tracks for intrusions
        for track_id, track in current_tracks.items():
            if track["class"] != "person":
                continue

            bbox = track["bbox"]
            confidence = track["confidence"]
            current_center = get_bbox_center(bbox)
            previous_center = previous_centers.get(track_id)
            activity = determine_activity(current_center, previous_center)
            previous_centers[track_id] = current_center

            inside = is_person_inside_restricted_area(bbox, restricted_area)
            if not inside:
                continue

            # Check cooldowns to prevent spamming for the same continuous event
            if track_id in alerted_ids:
                missing_frames[track_id] = 0
                continue

            if (now_sec - alert_cooldowns.get(track_id, 0)) < 45.0:
                missing_frames[track_id] = 0
                continue

            if active_recordings and (now_sec - last_global_alert_time) < GLOBAL_ALERT_COOLDOWN:
                continue

            # NEW GENUINE INTRUSION
            event = create_intrusion_event(
                processed_frame, track_id, confidence, activity
            )
            if event is None:
                continue

            # Send detection to dashboard
            send_detection_to_dashboard(event["event_data"])

            # 1. Send first frame immediately to Telegram
            alert_system.send_initial_alert(
                frame_path=event["image_path"],
                track_id=track_id,
                object_name="person",
                confidence=confidence,
                activity=activity,
                timestamp=event["event_data"]["timestamp"],
            )

            alerted_ids.add(track_id)
            alert_cooldowns[track_id] = now_sec
            last_global_alert_time = now_sec
            missing_frames[track_id] = 0

            # Start 2-minute video recording
            video_path = event["video_path"]
            fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)
            video_writer = cv2.VideoWriter(
                video_path,
                fourcc,
                source_fps,
                (frame_width, frame_height),
            )

            if not video_writer.isOpened():
                print(f"[ERROR] Could not start intrusion video recording: {video_path}")
                alert_system.update_alert_json(event["json_path"], False)
            else:
                recording_id = f"{event['event_data']['timestamp']}_ID{track_id}_{id(event)}"
                active_recordings[recording_id] = {
                    "writer": video_writer,
                    "start_time": time.time(),
                    "event": event,
                    "frame_2_sent": False,
                }
                video_writer.write(processed_frame)

        # Record frames and handle Frame 2 (+3s) and 2-min video completion
        finished_recordings = []
        for recording_id, recording in list(active_recordings.items()):
            writer = recording["writer"]
            start_time = recording["start_time"]
            event = recording["event"]

            writer.write(processed_frame)
            recording_elapsed = time.time() - start_time

            # Exactly 3 seconds after Frame 1: capture and send Frame 2 (no Frame 3!)
            if recording_elapsed >= 3.0 and not recording["frame_2_sent"]:
                frame_2_filename = f"intrusion_{event['event_data']['track_id']}_frame2.jpg"
                frame_2_path = os.path.join(INTRUSION_DIR, frame_2_filename)
                cv2.imwrite(frame_2_path, processed_frame)

                alert_system.send_update_frame(
                    frame_path=frame_2_path,
                    track_id=event["event_data"]["track_id"],
                    object_name=event["event_data"]["object"],
                    activity="Still inside restricted area",
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    frame_number=2,
                )
                recording["frame_2_sent"] = True

            # Complete after 2 minutes (120 seconds)
            if recording_elapsed >= INTRUSION_VIDEO_SECONDS:
                print(f"[INFO] 2-minute intrusion recording completed for Track ID {event['event_data']['track_id']}.")
                writer.release()
                video_path = event["video_path"]
                video_exists = os.path.exists(video_path)

                update_event_json(event["json_path"], event["event_data"], video_exists)

                if video_exists:
                    # Send 2-minute video to Telegram automatically
                    alert_system.send_completed_video(
                        video_path=video_path,
                        track_id=event["event_data"]["track_id"],
                        object_name=event["event_data"]["object"],
                        activity=event["event_data"]["activity"],
                        timestamp=event["event_data"]["timestamp"],
                    )
                    send_video_to_dashboard(event["det_id"], event["video_filename"])

                finished_recordings.append(recording_id)

        for rec_id in finished_recordings:
            active_recordings.pop(rec_id, None)

        # Handle missing tracks
        ids_to_remove = []
        for track_id in list(alerted_ids):
            if track_id in current_visible_ids:
                missing_frames[track_id] = 0
            else:
                missing_frames[track_id] = missing_frames.get(track_id, 0) + 1
                if missing_frames[track_id] >= TRACK_LOST_GRACE_FRAMES:
                    ids_to_remove.append(track_id)

        for track_id in ids_to_remove:
            alerted_ids.discard(track_id)
            missing_frames.pop(track_id, None)
            previous_centers.pop(track_id, None)

        # Header overlay for live preview
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            processed_frame,
            f"CAM-001 | {now_str} | Active Intrusions: {len(alerted_ids)}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
        )

        # Push processed frame to dashboard stream so it appears in Live CCTV section
        if (now_sec - last_push_time) > 0.04:  # ~25 FPS
            last_push_time = now_sec
            _, enc_buf = cv2.imencode(".jpg", processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            push_frame_to_dashboard(enc_buf.tobytes())

        # Optional preview window if enabled explicitly
        if SHOW_PREVIEW:
            cv2.imshow("FISHER AI CCTV - Intrusion Detection", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                running = False

except KeyboardInterrupt:
    print("\n[INFO] KeyboardInterrupt received.")
except Exception as error:
    print(f"[ERROR] Detection loop exception: {error}")
finally:
    print("[INFO] Releasing active resources...")
    for rec in active_recordings.values():
        try:
            rec["writer"].release()
        except Exception:
            pass
    active_recordings.clear()

    if cap:
        cap.release()
    detector.close()
    cv2.destroyAllWindows()
    print("[INFO] FISHER CCTV Detection process shut down gracefully.")
