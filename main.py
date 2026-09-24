"""
Analytics — video analytics pipeline.

Modules:
    1. Intrusion Detection      (IntrusionDetector)
    2. Crowd Counting           (CrowdCounter)
    3. Loitering Detection      (LoiteringDetector)
    4. Restricted Area Monitor  (RestrictedAreaMonitor)
    5. Event Classification     (EventClassifier)

Usage:
    python main.py --source 0 --config config.json --display
    python main.py --source path/to/video.mp4 --config config.json --output annotated.mp4
"""
import argparse
import json
import time
from importlib import import_module
from collections import OrderedDict
from typing import Any, Callable, cast

# The installed OpenCV package does not expose usable type information here.
cv2_api: Any = import_module("cv2")

from detector import PersonDetector
from tracker import CentroidTracker
from zones import load_zones as _load_zones  # type: ignore[reportUnknownVariableType]
from events import EventClassifier
from modules import IntrusionDetector, RestrictedAreaMonitor, LoiteringDetector, CrowdCounter

load_zones: Callable[[Any], list[Any]] = cast(
    Callable[[Any], list[Any]], _load_zones
)

ZONE_COLORS = {
    "restricted": (0, 0, 255),
    "watch": (0, 165, 255),
    "counting": (255, 200, 0),
}


def draw_overlays(
    frame: Any,
    zones: list[Any],
    tracked_objects: OrderedDict[int, tuple[float, float]],
    tracker: Any,
    crowd_count: int,
) -> Any:
    for zone in zones:
        color = ZONE_COLORS.get(zone.zone_type, (200, 200, 200))
        zone.draw(frame, color=color)
        cv2_api.putText(frame, zone.name, tuple(zone.polygon[0]),
                cv2_api.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    for oid, (cx, cy) in tracked_objects.items():
        dwell = tracker.duration(oid)
        cv2_api.circle(frame, (int(cx), int(cy)), 4, (0, 255, 0), -1)
        cv2_api.putText(frame, f"ID {oid} | {dwell:.0f}s", (int(cx) + 8, int(cy) - 8),
                cv2_api.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)

        cv2_api.putText(frame, f"Crowd count: {crowd_count}", (15, 30),
                cv2_api.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    return frame


def main():
    parser = argparse.ArgumentParser(description="Analytics video pipeline")
    parser.add_argument("--source", default="0", help="Video file path or webcam index")
    parser.add_argument("--config", default="config.json", help="Path to zone/config JSON")
    parser.add_argument("--output", default=None, help="Optional annotated video output path")
    parser.add_argument("--display", action="store_true", help="Show a live preview window")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    load_zones_api = load_zones
    zones = load_zones_api(config)
    detector: Any = PersonDetector(**config.get("detector", {}))
    tracker: Any = CentroidTracker()
    classifier: Any = EventClassifier()

    intrusion: Any = IntrusionDetector(zones, classifier)
    restricted: Any = RestrictedAreaMonitor(zones, classifier)
    loitering: Any = LoiteringDetector(
        zones, classifier, tracker,
        threshold_seconds=config.get("loitering_threshold_seconds", 15),
    )
    counting_zone: Any = next((z for z in zones if z.zone_type == "counting"), None)
    crowd: Any = CrowdCounter(classifier, threshold=config.get("crowd_threshold", 10), zone=counting_zone)

    source = int(args.source) if args.source.isdigit() else args.source
    cap: Any = cv2_api.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video source: {args.source}")

    writer = None
    if args.output:
        fourcc: Any = cv2_api.VideoWriter_fourcc(*"mp4v")
        fps = cap.get(cv2_api.CAP_PROP_FPS) or 20
        w = int(cap.get(cv2_api.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2_api.CAP_PROP_FRAME_HEIGHT))
        writer: Any = cv2_api.VideoWriter(args.output, fourcc, float(fps), (w, h))

    print("Analytics pipeline started. Press 'q' to quit (if --display).")
    frame_count = 0
    t0 = time.time()

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_count += 1

        detections = detector.detect(frame)
        centroids = [d.centroid for d in detections]
        tracked_objects = tracker.update(centroids)

        intrusion.update(tracked_objects)
        restricted.update(tracked_objects)
        loitering.update(tracked_objects)
        crowd_count = crowd.update(tracked_objects)

        frame = draw_overlays(frame, zones, tracked_objects, tracker, crowd_count)

        if writer:
            writer.write(frame)
        if args.display:
            cv2_api.imshow("Analytics", frame)
            if cv2_api.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    if writer:
        writer.release()
    cv2_api.destroyAllWindows()

    classifier.export_csv()
    elapsed = time.time() - t0
    print(
        f"Processed {frame_count} frames in {elapsed:.1f}s "
        f"({frame_count / max(elapsed, 0.001):.1f} FPS). "
        f"{len(classifier.events)} events logged to events_log.jsonl / events_log.csv"
    )


if __name__ == "__main__":
    main()
