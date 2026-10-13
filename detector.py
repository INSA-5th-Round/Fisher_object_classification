from ultralytics import YOLO

# Load model once
model = YOLO("yolov8n.pt")

def detect_objects(frame):

    results = model(frame, conf=0.5)

    detections = []

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            detections.append({
                "class": model.names[cls],
                "confidence": round(conf, 2)
            })

    return detections