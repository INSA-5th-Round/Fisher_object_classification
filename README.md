CCTV Frame Forwarder

This small Python client captures frames from a CCTV RTSP stream, optionally crops/resizes them, and sends JPEG frames to a detection HTTP endpoint. Its job is to get video from a camera, prepare frames, and send them to another server where the AI can process them.


Setup

1. Create a virtual environment and install dependencies:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r "c:\Users\Lenovo\Desktop\INSA PROJECT\requirements.txt"
```

Usage

```bash
python cctv_client.py --rtsp "rtsp://user:pass@camera-ip:554/stream" --url "http://localhost:8000/detect" --interval 0.2 --show
```

Options

- `--rtsp`: RTSP URL of the CCTV camera (required)
- `--url`: Detection server HTTP endpoint to POST frames (required)
- `--interval`: Seconds between sends (default 0.2)
- `--resize W H`: Resize before sending
- `--roi X Y W H`: Crop ROI before sending
- `--show`: Show preview window with ROI drawn
- `--auth user:pass`: Basic auth for detection server

Notes

- The detection server should accept a multipart form `image` field containing the JPEG.