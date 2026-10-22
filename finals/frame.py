import argparse
import cv2
import time
import signal
import sys

running = True


def signal_handler(sig, frame):
    global running
    print("\n[INFO] Stopping frame capture service...")
    running = False


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Capture frames from an RTSP or USB CCTV camera"
    )

    parser.add_argument(
        "--source",
        default="0",
        help="CCTV Camera index or RTSP URL (default: 0)",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=0.04,
        help="Seconds between frames (default: 0.04 ~25 FPS)",
    )

    parser.add_argument(
        "--resize",
        type=int,
        nargs=2,
        metavar=("W", "H"),
        help="Resize frames to WIDTH HEIGHT before sending",
    )

    parser.add_argument(
        "--show",
        action="store_true",
        help="Show desktop camera preview",
    )

    return parser.parse_args()


def main():
    global running

    args = parse_args()
    source = int(args.source) if args.source.isdigit() else args.source

    cap = cv2.VideoCapture(source, cv2.CAP_DSHOW) if isinstance(source, int) else cv2.VideoCapture(source)
    if not cap.isOpened():
        cap = cv2.VideoCapture(source)

    if not cap.isOpened():
        print(f"[ERROR] Failed to open video source: {source}")
        sys.exit(1)

    print(f"[INFO] Camera {source} connected. Interval: {args.interval}s")
    last_frame_time = 0.0

    try:
        while running:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[WARNING] Failed to read frame. Retrying...")
                time.sleep(0.1)
                continue

            current_time = time.time()
            if current_time - last_frame_time < args.interval:
                continue

            if args.resize:
                width, height = args.resize
                frame = cv2.resize(frame, (width, height))

            last_frame_time = current_time

            if args.show:
                cv2.imshow("FISHER CCTV Feed", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    running = False
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Camera frame capture stopped.")


if __name__ == "__main__":
    main()
