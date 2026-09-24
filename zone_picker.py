"""Interactive helper: click points on a video frame to define zone polygons.
Prints the resulting zones as JSON you can paste straight into config.json.

Usage:
    python zone_picker.py --source path/to/video.mp4

Controls:
    Left click  - add a point to the current polygon
    'n'         - finish current zone, start a new one
    's'         - finish current zone (if any) and print all zones as JSON
    'q'         - quit without printing
"""
import argparse
import json
import numpy as np
import cv2

zones = []
current_polygon = []


def on_mouse(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        current_polygon.append([x, y])


def to_np(poly):
    return np.array(poly, dtype=np.int32)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="0")
    args = parser.parse_args()

    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source)
    ok, frame = cap.read()
    cap.release()
    if not ok:
        raise RuntimeError("Could not read a frame from source")

    cv2.namedWindow("Zone Picker")
    cv2.setMouseCallback("Zone Picker", on_mouse)

    while True:
        display = frame.copy()
        for poly in zones:
            cv2.polylines(display, [to_np(poly)], True, (0, 165, 255), 2)
        if len(current_polygon) > 1:
            cv2.polylines(display, [to_np(current_polygon)], False, (0, 255, 0), 2)
        for pt in current_polygon:
            cv2.circle(display, tuple(pt), 4, (0, 255, 0), -1)

        cv2.imshow("Zone Picker", display)
        key = cv2.waitKey(20) & 0xFF

        if key == ord("n") and len(current_polygon) >= 3:
            zones.append(current_polygon.copy())
            current_polygon.clear()
        elif key == ord("s"):
            if len(current_polygon) >= 3:
                zones.append(current_polygon.copy())
                current_polygon.clear()
            output = {
                "zones": [
                    {"name": f"zone_{i}", "type": "restricted", "polygon": z}
                    for i, z in enumerate(zones)
                ]
            }
            print(json.dumps(output, indent=2))
            break
        elif key == ord("q"):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
