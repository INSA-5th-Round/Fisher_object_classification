import cv2
import time
import threading
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import numpy as np

from yolo_detector import ObjectDetector
import database

logger = logging.getLogger("cctv_backend.camera")


class CameraStreamManager:
    """
    Singleton Camera Stream Manager.
    Owns the physical camera device (index 0).
    Runs real YOLO detection on the PC camera feed.
    Serves live annotated frames and clean raw frames to other components.
    Accepts external custom frames when frame_and_detection.py is running.
    """
    _instance: Optional["CameraStreamManager"] = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, source: int = 0):
        if self._initialized:
            return
        self.source = source
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.cap: Optional[cv2.VideoCapture] = None

        self.current_frame_bytes: Optional[bytes] = None
        self.current_raw_frame_bytes: Optional[bytes] = None
        self.custom_frame_bytes: Optional[bytes] = None
        self.last_custom_frame_time: float = 0.0

        self.frame_lock = threading.Lock()
        self.use_fallback = False

        # YOLO object detector for live stream
        self.detector: Optional[ObjectDetector] = None
        try:
            self.detector = ObjectDetector(confidence=0.45)
            logger.info("Live stream ObjectDetector initialized.")
        except Exception as e:
            logger.warning(f"Could not initialize ObjectDetector in CameraStreamManager: {e}")

        # Detection persistence throttle
        self.last_detection_save_time = 0.0
        self.seen_track_cooldown: Dict[int, float] = {}

        self._generate_fallback_frame("INITIALIZING PC CAMERA...")
        self._initialized = True

    def start(self):
        """Start the background frame capture and detection thread."""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True, name="CameraCaptureThread")
        self.thread.start()
        logger.info(f"CameraStreamManager capture thread started (Source: {self.source})")

    def stop(self):
        """Stop capture thread and release camera."""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        with self.frame_lock:
            if self.cap:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
        logger.info("CameraStreamManager stopped and camera released.")

    def _init_camera(self) -> bool:
        """Attempt to open physical OpenCV VideoCapture."""
        try:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None

            # On Windows, try CAP_DSHOW first
            cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.source)

            if cap.isOpened():
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                self.cap = cap
                self.use_fallback = False
                logger.info("Physical PC camera opened successfully.")
                return True
        except Exception as e:
            logger.warning(f"Could not open physical camera: {e}")

        self.use_fallback = True
        return False

    def _generate_fallback_frame(self, status_msg: str = "LIVE FEED") -> bytes:
        """Generates a clean standby frame when physical camera is unavailable."""
        width, height = 640, 480
        frame = np.zeros((height, width, 3), dtype=np.uint8)

        for y in range(0, height, 40):
            cv2.line(frame, (0, y), (width, y), (25, 25, 25), 1)
        for x in range(0, width, 40):
            cv2.line(frame, (x, 0), (x, height), (25, 25, 25), 1)

        cv2.rectangle(frame, (10, 10), (width - 10, height - 10), (60, 60, 60), 1)

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, "CAM-001 [PC CAMERA]", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 128), 2)
        cv2.putText(frame, now_str, (width - 240, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        blink = int(time.time() * 2) % 2 == 0
        dot_color = (0, 0, 255) if blink else (100, 100, 100)
        cv2.circle(frame, (width - 260, 30), 6, dot_color, -1)
        cv2.putText(frame, "REC", (width - 295, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.45, dot_color, 1)

        box_top_left = (120, 190)
        box_bottom_right = (520, 290)
        cv2.rectangle(frame, box_top_left, box_bottom_right, (35, 35, 35), -1)
        cv2.rectangle(frame, box_top_left, box_bottom_right, (80, 80, 80), 1)

        cv2.putText(frame, "FISHER CCTV SURVEILLANCE", (140, 225), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(frame, f"STATUS: {status_msg}", (140, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 230, 255), 1)

        cv2.putText(frame, "AI INTRUSION DETECTION ACTIVE", (20, height - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)

        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        raw_bytes = buffer.tobytes()
        with self.frame_lock:
            self.current_frame_bytes = raw_bytes
            self.current_raw_frame_bytes = raw_bytes
        return raw_bytes

    def _capture_loop(self):
        """Continuous camera capture and detection loop."""
        retry_interval = 4.0
        last_retry = 0.0

        while self.running:
            # Check if custom frame injected from frame_and_detection.py within last 2.5 seconds
            now = time.time()
            if self.custom_frame_bytes and (now - self.last_custom_frame_time) < 2.5:
                # Custom frame active from external detector
                time.sleep(0.03)
                continue

            # Ensure camera is opened
            if self.cap is None or not self.cap.isOpened():
                if now - last_retry > retry_interval:
                    last_retry = now
                    self._init_camera()

            if self.cap and self.cap.isOpened():
                ret, raw_frame = self.cap.read()
                if ret and raw_frame is not None:
                    # Raw frame encoded for raw-stream
                    _, raw_buffer = cv2.imencode(".jpg", raw_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    raw_bytes = raw_buffer.tobytes()

                    # Process with YOLO detector if frame_and_detection is not overriding
                    annotated_frame = raw_frame.copy()
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if self.detector:
                        try:
                            annotated_frame = self.detector.process_frame(annotated_frame, draw=True)
                            tracks = self.detector.get_tracks()
                            self._handle_detected_tracks(tracks, raw_frame, now_str)
                        except Exception as e:
                            logger.debug(f"Detector processing error: {e}")

                    # Header timestamp and camera tag
                    cv2.putText(
                        annotated_frame,
                        f"CAM-001 | {now_str}",
                        (15, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                    _, ann_buffer = cv2.imencode(".jpg", annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                    ann_bytes = ann_buffer.tobytes()

                    with self.frame_lock:
                        self.current_frame_bytes = ann_bytes
                        self.current_raw_frame_bytes = raw_bytes

                    time.sleep(0.033)  # ~30 FPS
                    continue
                else:
                    logger.warning("Camera frame read failed. Releasing device.")
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                    self.cap = None

            # Fallback when physical camera is offline
            fb = self._generate_fallback_frame("CAMERA STANDBY")
            time.sleep(0.1)

    def _handle_detected_tracks(self, tracks: Dict[int, Dict[str, Any]], raw_frame: np.ndarray, timestamp_str: str):
        """Persists genuine detections into MongoDB if throttled."""
        now = time.time()
        for track_id, info in tracks.items():
            class_name = info.get("class", "object")
            conf = info.get("confidence", 0.5)

            # Throttle detection events per track ID (10s) and globally (2s)
            last_seen = self.seen_track_cooldown.get(track_id, 0.0)
            if (now - last_seen) > 10.0 and (now - self.last_detection_save_time) > 2.0:
                self.seen_track_cooldown[track_id] = now
                self.last_detection_save_time = now

                # Save detection snapshot
                clean_time = timestamp_str.replace(" ", "T").replace(":", "-")
                filename = f"det_{clean_time}_ID{track_id}.jpg"
                filepath = settings.INTRUSIONS_DIR / filename
                try:
                    cv2.imwrite(str(filepath), raw_frame)
                except Exception:
                    filename = None

                det_id = f"DET-{clean_time}-{track_id}"
                event = {
                    "id": det_id,
                    "cameraId": "CAM-001",
                    "type": f"{class_name.capitalize()} detected",
                    "confidence": round(conf * 100, 1),
                    "severity": "high" if class_name == "person" else "medium",
                    "timestamp": timestamp_str,
                    "status": "new",
                    "image": filename,
                    "imageUrl": f"/media/intrusions/{filename}" if filename else None,
                    "description": f"Object: {class_name}; Track ID: {track_id}; Confidence: {round(conf*100, 1)}%",
                }
                try:
                    database.save_detection(event)
                    logger.info(f"Persisted real detection event {det_id} ({class_name}) to database.")
                except Exception as e:
                    logger.warning(f"Could not persist detection event: {e}")

    def set_custom_frame(self, frame_bytes: bytes):
        """Allows frame_and_detection.py to inject live annotated frames with restricted area & tracking."""
        with self.frame_lock:
            self.custom_frame_bytes = frame_bytes
            self.last_custom_frame_time = time.time()

    def get_frame(self) -> bytes:
        """Returns the latest annotated frame for dashboard display."""
        now = time.time()
        with self.frame_lock:
            if self.custom_frame_bytes and (now - self.last_custom_frame_time) < 2.5:
                return self.custom_frame_bytes
            if self.current_frame_bytes is not None:
                return self.current_frame_bytes
        return self._generate_fallback_frame("STREAM READY")

    def get_raw_frame(self) -> bytes:
        """Returns clean raw camera frame without bounding box overlays."""
        with self.frame_lock:
            if self.current_raw_frame_bytes is not None:
                return self.current_raw_frame_bytes
        return self._generate_fallback_frame("RAW FEED READY")


# Global singleton instance
camera_stream_manager = CameraStreamManager()
