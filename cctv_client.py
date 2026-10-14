import argparse #Let the user give information when starting the program.takes instructions from the terminal
import cv2 # main video/image tool
import requests # Send frames to your AI/server
import time # Control timing and intervals
import signal # Handle things like Ctrl+C safely
import sys # Control/interact with Python itself

running = True

# Function is used to stop  CCTV program safely when pressing  Ctrl + C.
def signal_handler(sig, frame):
    global running
    running = False

# When you receive either SIGIN,SIGTERM use my signal_handler to stop the program safely.
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


#
def parse_args():
    p = argparse.ArgumentParser(description="Capture frames from RTSP and send to detection API")
    p.add_argument("--rtsp", required=True, help="RTSP URL of the CCTV camera") #Which CCTV camera should I connect to?
    p.add_argument("--url", required=True, help="Detection server HTTP endpoint to POST frames") #Where should I send the frames?
    p.add_argument("--interval", type=float, default=0.2, help="Seconds between sends (default 0.2)")  #1 ÷ 0.2 = 5 frames/second how often to send a frame.
    p.add_argument("--resize", type=int, nargs=2, metavar=("W","H"), help="Resize frames to WIDTH HEIGHT before sending") #to change the frame size
    p.add_argument("--roi", type=int, nargs=4, metavar=("X","Y","W","H"), help="Crop ROI x y w h before sending") #Region of Interest To select only a specific part of the CCTV image.
    p.add_argument("--show", action="store_true", help="Show preview window with framing") #show me a live preview
    p.add_argument("--auth", help="Optional Basic auth user:pass for detection server") #to provide a username and password for the detection server.
    return p.parse_args()


def main():
    args = parse_args()

    cap = cv2.VideoCapture(args.rtsp) #Open this video source. connection to the video stream.
    if not cap.isOpened():
        print("Failed to open RTSP stream:", args.rtsp)
        sys.exit(1)

    auth = None
    if args.auth:
        if ":" in args.auth:
            user, pwd = args.auth.split(":", 1)
            auth = (user, pwd)

    last_send = 0.0 #This stores the time when the previous frame was sent.


# If reading the frame failed OR there is no frame... Wait half a second and try again
    while running:
        ret, frame = cap.read()
        if not ret or frame is None:
            # wait a bit and retry
            time.sleep(0.5)
            continue

        # apply ROI ,This can reduce unnecessary information before sending the frame to the AI.
        send_frame = frame
        if args.roi:
            x, y, w, h = args.roi
            send_frame = send_frame[y : y + h, x : x + w]

        # resize
        if args.resize:
            w, h = args.resize
            send_frame = cv2.resize(send_frame, (w, h))

        # preview
        if args.show:
            preview = frame.copy()
            if args.roi:
                x, y, w, h = args.roi
                cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.imshow("CCTV Preview", preview)
            if cv2.waitKey(1) & 0xFF == ord('q'):  #Press q to stop
                break

        now = time.time()
        if now - last_send < args.interval:
            # throttle sending
            time.sleep(max(0.0, args.interval - (now - last_send)))

        # encode as JPEG
        ok, jpg = cv2.imencode('.jpg', send_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
        if not ok:
            print("Failed to encode frame")
            continue
        data = jpg.tobytes() #This turns the encoded JPEG into bytes.

        try:
            files = {'image': ('frame.jpg', data, 'image/jpeg')} #Prepare the image for HTTP
            # send POST; adjust if detection API expects JSON or base64
            resp = requests.post(args.url, files=files, auth=auth, timeout=5) #sends an HTTP POST request to your detection server
            try:
                print('Server response:', resp.status_code, resp.text)
            except Exception:
                print('Server response code:', resp.status_code)
        except requests.exceptions.RequestException as e: # Network error handling
            print('Send error:', e)

        last_send = time.time()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
