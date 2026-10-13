import cv2
import requests
import time
from detector import detect_objects


VIDEO = "test_frame2.mp4"
SERVER_URL = "http://127.0.0.1:5000/detect"

# # ROI: x, y, width, height
# x1 = 80
# y1 = 0
# x2= 400
# y2 = 350

# Resize after cropping
resize_width = 400
resize_height = 200

# Send one frame every 0.5 seconds
interval = 0.5


# -----------------------------
# OPEN VIDEO
# -----------------------------

cap = cv2.VideoCapture(VIDEO)

if not cap.isOpened():
    print("Could not open video:")
    exit()

print("Video opened successfully")


# -----------------------------
# MAIN LOOP
# -----------------------------

last_send = 0

while True:

    # Read one frame
    ret, frame = cap.read()

    if not ret:
        print("End of video")
        break
    detections = detect_objects(frame)

    print("Detections:", detections)


    # -------------------------
    # ROI
    # -------------------------

    # roi = frame[
    #     y1:y2,
    #     x1:x2
    # ]

    # -------------------------
    # RESIZE
    # # -------------------------

    # resized = cv2.resize(
    #     roi,
    #     (resize_width, resize_height)
    # )

    # -------------------------
    # SHOW PREVIEW
    # -------------------------

    # preview = frame.copy()

    # cv2.rectangle(
    #     preview,
    #     (x1, y1),
    #     (x2, y2),
    #     (0, 255, 0),
    #     2
    # )

    # cv2.imshow("CCTV Preview", preview)
    # cv2.imshow("ROI Sent to Server", resized)

    # Press Q to stop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

    # -------------------------
    # CONTROL SEND INTERVAL
    # -------------------------

    now = time.time()

    if now - last_send < interval:
        continue

    # -------------------------
    # CONVERT FRAME TO JPEG
    # -------------------------

    ok, jpg = cv2.imencode(
        ".jpg",
         frame,
         [int(cv2.IMWRITE_JPEG_QUALITY), 85]
    )

    if not ok:
        print("JPEG encoding failed")
        continue

    # Convert JPEG to bytes
    data = jpg.tobytes()





    # -------------------------
    # SEND TO SERVER
    # -------------------------

    files = {
        "image": (
            "frame.jpg",
            data,
            "image/jpeg"
        )
    }

    try:

        response = requests.post(
            SERVER_URL,
            files=files,
            timeout=5
        )

        print(
            "Frame sent | Server:",
            response.status_code,
            "|",
            response.text
        )

    except requests.exceptions.RequestException as e:

        print("Send error:", e)

    last_send = time.time()





# -----------------------------
# CLEANUP
# -----------------------------

cap.release()
cv2.destroyAllWindows()

print("Camera program stopped")
