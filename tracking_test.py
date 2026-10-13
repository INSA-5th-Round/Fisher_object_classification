import os
import time
from datetime import datetime

import cv2
from ultralytics import YOLO

from alerts import AlertManager
from alerts.models import AlertEvent


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "yolov8n.pt"

CONFIDENCE_THRESHOLD = 0.50
COOLDOWN_SECONDS = 30

SCREENSHOT_DIR = "screenshots"


# ============================================================
# ALLOWED OBJECT CLASSES
# ============================================================

ALLOWED_CLASSES = {
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "bus",
    "train",
    "truck",
    "boat",
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe",
}


# ============================================================
# ACTIVITY DETECTION
# ============================================================

def detect_activity(previous_center, current_center):
    """
    Determine simple movement activity by comparing
    the object's previous and current center positions.

    Returns:
        UNKNOWN
        STATIONARY
        MOVING
    """

    if previous_center is None:
        return "UNKNOWN"

    dx = current_center[0] - previous_center[0]
    dy = current_center[1] - previous_center[1]

    distance = (dx ** 2 + dy ** 2) ** 0.5

    if distance < 5:
        return "STATIONARY"

    return "MOVING"


# ============================================================
# SAVE DETECTION SCREENSHOT
# ============================================================

def save_detection_screenshot(
    frame,
    class_name,
    confidence
):
    os.makedirs(
        SCREENSHOT_DIR,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    filename = (
        f"{class_name}_"
        f"{confidence * 100:.0f}_"
        f"{timestamp}.jpg"
    )

    filepath = os.path.join(
        SCREENSHOT_DIR,
        filename
    )

    success = cv2.imwrite(
        filepath,
        frame
    )

    if not success:
        print(
            f"[ERROR] Could not save screenshot: "
            f"{filepath}"
        )
        return None

    print(
        f"[SCREENSHOT] Saved: {filepath}"
    )

    return filepath


# ============================================================
# CREATE FISHER ALERT
# ============================================================

def create_fisher_alert(
    alert_manager,
    class_name,
    confidence,
    screenshot_path,
    activity
):
    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    severity = "HIGH"

    message = (
        f"{class_name.capitalize()} detected "
        f"by YOLOv8. "
        f"Confidence: {confidence * 100:.1f}%. "
        f"Activity: {activity}."
    )

    event = AlertEvent(
        event_type=f"{class_name.capitalize()} Detected",
        camera="Camera 01",
        confidence=confidence,
        timestamp=timestamp,
        severity=severity,
        screenshot_path=screenshot_path,
        message=message
    )

    print()
    print("=" * 60)
    print("[ALERT] FISHER Alert Generated")
    print("=" * 60)
    print(f"Object:       {class_name}")
    print(f"Confidence:   {confidence * 100:.1f}%")
    print(f"Activity:     {activity}")
    print(f"Severity:     {severity}")
    print(f"Time:         {timestamp}")
    print(f"Screenshot:   {screenshot_path}")
    print("=" * 60)

    result = alert_manager.send_alert(event)

    print()
    print("[ALERT RESULT]")
    print(result)
    print()

    return result


# ============================================================
# OBJECT DETECTION + TRACKING
# ============================================================

def detect_objects_in_video(
    video_source=0,
    output_file="output.mp4"
):
    """
    Detect and track objects from a webcam or video file.

    Flow:

        Camera
          ↓
        OpenCV
          ↓
        Frame
          ↓
        YOLOv8 Tracking
          ↓
        Object + Confidence + Track ID
          ↓
        Position comparison
          ↓
        Activity
          ↓
        Screenshot
          ↓
        FISHER AlertManager
          ↓
        Telegram / Email / SMS
    """

    # --------------------------------------------------------
    # LOAD YOLO MODEL
    # --------------------------------------------------------

    print(
        f"[YOLO] Loading model: {MODEL_PATH}"
    )

    model = YOLO(
        MODEL_PATH
    )

    print(
        "[YOLO] Model loaded successfully."
    )

    # --------------------------------------------------------
    # INITIALIZE ALERT MANAGER
    # --------------------------------------------------------

    print(
        "[FISHER] Initializing AlertManager..."
    )

    alert_manager = AlertManager()

    print(
        "[FISHER] AlertManager ready."
    )

    # --------------------------------------------------------
    # COOLDOWN STORAGE
    # --------------------------------------------------------

    last_alert_time = {}

    # Store previous center position
    # for each tracked object
    previous_centers = {}

    # --------------------------------------------------------
    # OPEN VIDEO SOURCE
    # --------------------------------------------------------

    cap = cv2.VideoCapture(
        video_source
    )

    if not cap.isOpened():
        print(
            "[ERROR] Could not open video source."
        )
        return

    print(
        f"[CAMERA] Video source opened: "
        f"{video_source}"
    )

    # --------------------------------------------------------
    # VIDEO PROPERTIES
    # --------------------------------------------------------

    frame_width = int(
        cap.get(
            cv2.CAP_PROP_FRAME_WIDTH
        )
    )

    frame_height = int(
        cap.get(
            cv2.CAP_PROP_FRAME_HEIGHT
        )
    )

    fps = cap.get(
        cv2.CAP_PROP_FPS
    )

    if fps <= 0:
        fps = 30

    print(
        f"[VIDEO] Resolution: "
        f"{frame_width}x{frame_height}"
    )

    print(
        f"[VIDEO] FPS: {fps}"
    )

    # --------------------------------------------------------
    # OUTPUT VIDEO
    # --------------------------------------------------------

    fourcc = cv2.VideoWriter_fourcc(
        *"mp4v"
    )

    out = cv2.VideoWriter(
        output_file,
        fourcc,
        fps,
        (
            frame_width,
            frame_height
        )
    )

    print(
        f"[VIDEO] Output file: "
        f"{output_file}"
    )

    # --------------------------------------------------------
    # START MESSAGE
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "FISHER YOLO OBJECT DETECTION + TRACKING"
    )
    print("=" * 60)

    print(
        "Press 'q' to quit."
    )

    print("=" * 60)
    print()

    # ========================================================
    # MAIN LOOP
    # ========================================================

    while True:

        # ----------------------------------------------------
        # READ FRAME
        # ----------------------------------------------------

        ret, frame = cap.read()

        if not ret:
            print(
                "[CAMERA] End of video stream "
                "or error reading frame."
            )
            break

        # ----------------------------------------------------
        # YOLO TRACKING
        # ----------------------------------------------------

        results = model.track(
            frame,
            persist=True,
            verbose=False
        )[0]

        # ----------------------------------------------------
        # PROCESS EACH DETECTION
        # ----------------------------------------------------

        for result in results.boxes:

            # -----------------------------------------------
            # BOUNDING BOX
            # -----------------------------------------------

            xyxy = (
                result.xyxy[0]
                .cpu()
                .numpy()
            )

            # -----------------------------------------------
            # CONFIDENCE
            # -----------------------------------------------

            confidence = float(
                result.conf[0]
            )

            # -----------------------------------------------
            # CLASS ID
            # -----------------------------------------------

            class_id = int(
                result.cls[0]
            )

            # -----------------------------------------------
            # CLASS NAME
            # -----------------------------------------------

            class_name = model.names[
                class_id
            ]

            # -----------------------------------------------
            # TRACK ID
            # -----------------------------------------------

            if result.id is not None:
                track_id = int(
                    result.id[0]
                )
            else:
                track_id = None

            # -----------------------------------------------
            # FILTER CLASS
            # -----------------------------------------------

            if class_name not in ALLOWED_CLASSES:
                continue

            # -----------------------------------------------
            # FILTER CONFIDENCE
            # -----------------------------------------------

            if confidence < CONFIDENCE_THRESHOLD:
                continue

            # -----------------------------------------------
            # BOX COORDINATES
            # -----------------------------------------------

            x1, y1, x2, y2 = map(
                int,
                xyxy
            )

            # -----------------------------------------------
            # OBJECT CENTER
            # -----------------------------------------------

            center_x = (
                x1 + x2
            ) // 2

            center_y = (
                y1 + y2
            ) // 2

            current_center = (
                center_x,
                center_y
            )

            # -----------------------------------------------
            # ACTIVITY
            # -----------------------------------------------

            if track_id is not None:

                previous_center = (
                    previous_centers.get(
                        track_id
                    )
                )

                activity = detect_activity(
                    previous_center,
                    current_center
                )

                previous_centers[
                    track_id
                ] = current_center

            else:

                previous_center = None
                activity = "UNKNOWN"

            # -----------------------------------------------
            # TERMINAL INFORMATION
            # -----------------------------------------------

            print(
                f"Object: {class_name} | "
                f"Confidence: {confidence:.2f} | "
                f"Track ID: {track_id} | "
                f"Activity: {activity}"
            )

            # -----------------------------------------------
            # DRAW BOUNDING BOX
            # -----------------------------------------------

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # -----------------------------------------------
            # DISPLAY LABEL
            # -----------------------------------------------

            label = (
                f"{class_name} "
                f"ID:{track_id} "
                f"{confidence * 100:.1f}% "
                f"{activity}"
            )

            cv2.putText(
                frame,
                label,
                (
                    x1,
                    max(
                        y1 - 10,
                        20
                    )
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

            # -----------------------------------------------
            # COOLDOWN
            # -----------------------------------------------

            current_time = time.time()

            last_time = (
                last_alert_time.get(
                    class_name,
                    0
                )
            )

            elapsed = (
                current_time -
                last_time
            )

            # -----------------------------------------------
            # SEND ALERT
            # -----------------------------------------------

            if (
                elapsed >=
                COOLDOWN_SECONDS
            ):

                screenshot_path = (
                    save_detection_screenshot(
                        frame,
                        class_name,
                        confidence
                    )
                )

                if screenshot_path is None:
                    continue

                create_fisher_alert(
                    alert_manager=alert_manager,
                    class_name=class_name,
                    confidence=confidence,
                    screenshot_path=screenshot_path,
                    activity=activity
                )

                last_alert_time[
                    class_name
                ] = current_time

            # -----------------------------------------------
            # COOLDOWN MESSAGE
            # -----------------------------------------------

            else:

                remaining = (
                    COOLDOWN_SECONDS -
                    elapsed
                )

                print(
                    f"[COOLDOWN] "
                    f"{class_name}: "
                    f"{remaining:.1f}s remaining",
                    end="\r"
                )

        # ----------------------------------------------------
        # SAVE OUTPUT FRAME
        # ----------------------------------------------------

        out.write(
            frame
        )

        # ----------------------------------------------------
        # DISPLAY FRAME
        # ----------------------------------------------------

        cv2.imshow(
            "FISHER YOLOv8 Object Detection + Tracking",
            frame
        )

        # ----------------------------------------------------
        # QUIT
        # ----------------------------------------------------

        if (
            cv2.waitKey(1) & 0xFF
            == ord("q")
        ):

            print()
            print(
                "[SYSTEM] Quit requested."
            )

            break

    # ========================================================
    # CLEANUP
    # ========================================================

    cap.release()

    out.release()

    cv2.destroyAllWindows()

    print()
    print("=" * 60)
    print(
        "FISHER YOLO DETECTION + TRACKING STOPPED"
    )
    print("=" * 60)

    print(
        f"Video saved to: "
        f"{output_file}"
    )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":

    detect_objects_in_video(
        video_source=0,
        output_file="output.mp4"
    )
