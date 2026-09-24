# Analytics — Video Analytics Toolkit

A modular video analytics pipeline built on OpenCV + YOLOv8, covering:

1. **Intrusion Detection** — alerts the moment a person first enters a monitored zone.
2. **Crowd Counting** — counts people in the full frame or a specific zone, alerts past a threshold.
3. **Loitering Detection** — flags anyone who stays inside a zone longer than a time limit.
4. **Restricted Area Monitor** — continuously (rate-limited) alerts while someone is inside a no-go zone.
5. **Event Classification** — every alert from the modules above is normalized into a typed
   `Event` (type, severity, zone, object id, timestamp) and logged to `events_log.jsonl` /
   `events_log.csv`.


- `detector.py` — wraps a YOLOv8 model, filtered to the COCO "person" class.
- `tracker.py` — simple centroid tracker; gives each person a persistent ID and tracks
  how long they've been visible (needed for loitering/dwell time).
- `zones.py` — polygon zones loaded from `config.json`; `Zone.contains(point)` does the
  point-in-polygon test.
- `modules.py` — the four detection modules, each just watching tracked centroids against zones.
- `events.py` — shared `EventClassifier` all modules report to; assigns severity and persists a log.
- `main.py` — wires everything together, reads a video/webcam, draws overlays, writes output.
- `zone_picker.py` — click-to-draw helper to generate zone polygons for your own footage.

## Setup

```bash
pip install -r requirements.txt
```

The first run will auto-download `yolov8n.pt` (the small/fast YOLOv8 model). Swap in
`yolov8s.pt` / `yolov8m.pt` in `config.json` for more accuracy at the cost of speed, or point
`model_path` at a custom-trained weights file.


`type` controls which module reacts to it:

| type        | used by                                    |
|-------------|---------------------------------------------|
| `watch`     | Intrusion Detection (edge-triggered, once)   |
| `restricted`| Restricted Area Monitor (continuous alerts)  |
| `counting`  | Crowd Counting (counts people inside it)     |

Loitering Detection watches every zone regardless of type.

Don't want to guess coordinates by hand? Run:

```bash
python zone_picker.py --source your_video.mp4
```

Click to place points, press `n` for a new zone, `s` to finish and print ready-to-paste JSON.

## Run it

```bash
# Webcam, live preview
python main.py --source 0 --display

# A video file, save an annotated copy, no preview window
python main.py --source input.mp4 --output annotated.mp4

# Custom config
python main.py --source 0 --config my_config.json --display
```

Alerts print to the console in real time and are written to:
- `events_log.jsonl` — one JSON object per line, easy to tail/stream
- `events_log.csv` — full run summary, written when the pipeline exits

## Tuning

In `config.json`:
- `crowd_threshold` — headcount that triggers a Crowd Counting alert.
- `loitering_threshold_seconds` — how long someone must dwell in a zone before it's "loitering".
- `detector.conf_threshold` — YOLO confidence cutoff (raise to reduce false positives).

In `modules.py`, each module also takes a `cooldown` (seconds) controlling how often it's
allowed to re-alert for the same object/zone, so you don't get spammed every frame.

## Notes / extending it

- Swap `PersonDetector` for any other YOLO class (e.g. vehicles) by changing `person_class_id`
  and the config's model.
- The tracker is intentionally simple (centroid distance matching) — for crowded scenes with
  lots of occlusion, consider swapping in a stronger tracker (e.g. ByteTrack, which ships with
  `ultralytics` as `model.track(...)`).
- Everything reports through `EventClassifier`, so adding a 6th module (e.g. line-crossing,
  abandoned-object detection) just means writing a new class in `modules.py` that calls
  `classifier.classify(...)`.
# CCTV-analytics
#### Sitota Getahun (rexdr)
