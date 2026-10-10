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

# Minimum time between alerts for the same object type.
# Example:
# person detected -> alert
# person detected again immediately -> ignored
# after 30 seconds -> another person alert is allowed
COOLDOWN_SECONDS = 30

SCREENSHOT_DIR = "screenshots"


# ============================================================
# OBJECTS WE WANT TO DETECT
# ============================================================

ALLOWED_CLASSES = {
    # Person
    "person",

    # Vehicles
    "bicycle",
    "car",
    "motorcycle",
    "bus",
    "train",
    "truck",
    "boat",

    # Animals
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
# SCREENSHOT FUNCTION
# ============================================================

def save_detection_screenshot(frame, class_name, confidence):
    """
    Save a screenshot when an alert is generated.

    Returns:
        Path of saved screenshot.
    """

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

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
    track_id=None,
    action="Unknown",
    speed=0.0
):
    """
    Create an AlertEvent and send it through
    the existing FISHER AlertManager.

    AlertManager is responsible for:
        - Telegram
        - SMS
        - Email
        - logging
    """

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    # Determine severity.
    #
    # Person/vehicle/animal detection itself
    # is currently treated as HIGH for this MVP.
    severity = "HIGH"

    message = (
        f"{class_name.capitalize()} detected by YOLOv8. "
        f"Confidence: {confidence * 100:.1f}%."
        f"Track ID : {track_id}. "
        f"Activity: {action}. "
        f"Speed: {speed:.1f}pixels/second."
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
# MAIN DETECTION FUNCTION
# ============================================================

def detect_objects_in_video(
    video_source=0,
    output_file="output.mp4"
):
    """
    Detect objects from a webcam or video file.

    Flow:

        Camera
          ↓
        YOLOv8
          ↓
        Detection
          ↓
        Screenshot
          ↓
        FISHER AlertManager
          ↓
        Telegram / SMS / Email
    """

    # --------------------------------------------------------
    # LOAD YOLO MODEL
    # --------------------------------------------------------

    print(
        f"[YOLO] Loading model: {MODEL_PATH}"
    )

    model = YOLO(MODEL_PATH)

    print("[YOLO] Model loaded successfully.")

    # --------------------------------------------------------
    # CREATE FISHER ALERT MANAGER
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

    # Example:
    #
    # {
    #     "person": 1727881234.55,
    #     "car": 1727881250.12
    # }
    #
    # This prevents the same object type from
    # generating an alert on every frame.

    last_alert_time = {}

    # Store previous position and time for each tracked object
    previous_positions = {}

    # --------------------------------------------------------
    # OPEN CAMERA / VIDEO
    # --------------------------------------------------------

    cap = cv2.VideoCapture(video_source)

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
    # GET VIDEO PROPERTIES
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

    # Webcam/video sources sometimes
    # report FPS as 0.

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
    # CREATE OUTPUT VIDEO
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

    print()
    print("=" * 60)
    print("FISHER YOLO OBJECT DETECTION")
    print("=" * 60)
    print("Press 'q' to quit.")
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
        # RUN YOLO
        # ----------------------------------------------------

        results = model.track(
            frame,
            persist=True,
            verbose=False
        )[0]

        # ----------------------------------------------------
        # PROCESS DETECTIONS
        # ----------------------------------------------------

        for result in results.boxes:

            # Bounding box
            xyxy = (
                result.xyxy[0]
                .cpu()
                .numpy()
            )

            # Track ID
            if result.id is None:
                continue

            track_id = int(result.id[0])

            # Confidence
            confidence = float(
                result.conf[0]
            )

            # Class ID
            class_id = int(
                result.cls[0]
            )

            # Class name
            class_name = model.names[
                class_id
            ]

            # ------------------------------------------------
            # FILTER OBJECT
            # ------------------------------------------------

            if (
                class_name not in
                ALLOWED_CLASSES
            ):
                continue

            # ------------------------------------------------
            # FILTER CONFIDENCE
            # ------------------------------------------------

            if (
                confidence <
                CONFIDENCE_THRESHOLD
            ):
                continue

            # ------------------------------------------------
            # BOUNDING BOX
            # ------------------------------------------------

            x1, y1, x2, y2 = map(
                int,
                xyxy
            )

            # Calculate center of the bounding box
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2 

            # ------------------------------------------------
            # CALCULATE MOVMENT 
            # ------------------------------------------------

            current_time = time.time()

            previous = previous_positions.get(track_id)

            speed = 0.0 

            if previous is not None:
                previous_x, previous_y, previous_time = previous

                distance = (
                (center_x - previous_x) ** 2
                + (center_y - previous_y) ** 2
                ) ** 0.5

                time_difference = current_time - previous_time

                if time_difference > 0:
                    speed = distance / time_difference

            # Save current position for the next frame
            previous_positions[track_id] = (
                center_x,
                center_y,
                current_time
            )

            # Determine activity from speed 
            if speed < 20:
                action = "Stationary"
            elif speed < 150:
                action = "Moving"
            else:
                action = "Moving Fast"

            # ------------------------------------------------
            # DRAW BOUNDING BOX
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            # Determine activity from speed
            if speed < 20:
                action = "Stationary"
            elif speed < 150:
                action = "Moving"
            else: 
                action = "Moving Fast"

            # ------------------------------------------------
            # DETECTION LABEL
            # ------------------------------------------------
            label = (
                f"{class_name} "
                f"ID:{track_id} "
                f"{confidence * 100:.1f}% "
                f"{action} "
                f"{speed:.1f}px/s"
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

            # ------------------------------------------------
            # CHECK ALERT COOLDOWN
            # ------------------------------------------------

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

            # ------------------------------------------------
            # GENERATE ALERT
            # ------------------------------------------------

            if (
                elapsed >=
                COOLDOWN_SECONDS
            ):

                # Save annotated screenshot.
                screenshot_path = (
                    save_detection_screenshot(
                        frame,
                        class_name,
                        confidence
                    )
                )

                # If screenshot failed,
                # do not generate alert.
                if screenshot_path is None:

                    continue

                # Send through existing
                # FISHER AlertManager.
                create_fisher_alert(
                    alert_manager=alert_manager,
                    class_name=class_name,
                    confidence=confidence,
                    screenshot_path=screenshot_path
                )

                # Update cooldown.
                last_alert_time[
                    class_name
                ] = current_time

            else:

                # Optional terminal message
                # showing cooldown state.

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
        # SAVE PROCESSED FRAME
        # ----------------------------------------------------

        out.write(frame)

        # ----------------------------------------------------
        # DISPLAY LIVE CAMERA
        # ----------------------------------------------------

        cv2.imshow(
            "FISHER YOLOv8 Object Detection",
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
    print("FISHER YOLO DETECTION STOPPED")
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
 