import os
import cv2
from pathlib import Path
from ultralytics import YOLO


class ObjectDetector:
    def __init__(
        self,
        confidence=0.5,
        model_path="yolov8n.pt",
        tracker_config="custom_botsort.yaml",
    ):
        self.confidence = confidence
        self.tracker_config = tracker_config

        # Resolve paths
        base_dir = Path(__file__).resolve().parent
        resolved_model = str(base_dir / model_path) if not os.path.isabs(model_path) and (base_dir / model_path).exists() else model_path
        resolved_tracker = str(base_dir / tracker_config) if not os.path.isabs(tracker_config) and (base_dir / tracker_config).exists() else tracker_config

        # Load YOLO model
        self.model = YOLO(resolved_model)
        self.resolved_tracker = resolved_tracker

        # Tracks visible in the current frame
        self.tracks = {}

        # Classes we allow the detector to report
        self.allowed_classes = {
            "person",
            "car",
            "motorcycle",
            "bus",
            "truck",
            "bicycle",
            "bird",
            "toy",
            "cat",
            "dog",
            "horse",
            "sheep",
            "cow",
            "elephant",
            "bear",
            "zebra",
            "giraffe",
            "backpack",
            "handbag",
            "suitcase",
            "table",
            "chair",
            "bottle",
            "bag",
            "cell phone",
            "laptop",
            "book",
            "umbrella",
        }

    def process_frame(self, frame, draw=True):
        """
        Run YOLO detection and BoT-SORT tracking.

        Returns:
            processed frame with bounding boxes drawn.
        """
        try:
            results = self.model.track(
                frame,
                persist=True,
                tracker=self.resolved_tracker,
                conf=self.confidence,
                verbose=False,
            )[0]
        except Exception:
            # Fallback to standard detect if tracking fails
            try:
                results = self.model(frame, conf=self.confidence, verbose=False)[0]
            except Exception:
                self.tracks = {}
                return frame

        current_tracks = {}

        if results.boxes is None or len(results.boxes) == 0:
            self.tracks = {}
            return frame

        boxes = results.boxes.xyxy.cpu().numpy()
        track_ids = (
            results.boxes.id.cpu().numpy().astype(int)
            if results.boxes.id is not None
            else [i + 1 for i in range(len(boxes))]
        )
        class_ids = results.boxes.cls.cpu().numpy().astype(int)
        confidences = results.boxes.conf.cpu().numpy()

        for box, track_id, class_id, conf in zip(
            boxes, track_ids, class_ids, confidences
        ):
            class_name = self.model.names[class_id]

            if class_name not in self.allowed_classes:
                continue

            if conf < self.confidence:
                continue

            x1, y1, x2, y2 = map(int, box)

            current_tracks[int(track_id)] = {
                "track_id": int(track_id),
                "class": class_name,
                "confidence": float(conf),
                "bbox": (x1, y1, x2, y2),
            }

            if draw:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                label = f"{class_name} ID:{track_id} {conf:.2f}"
                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

        self.tracks = current_tracks
        return frame

    def get_tracks(self):
        """Return currently visible tracks."""
        return self.tracks

    def close(self):
        """Clean up model resources."""
        self.tracks.clear()
