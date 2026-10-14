import cv2

cap = cv2.VideoCapture("test_frame2.mp4")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Resize the frame with width 400 and height 200
    resized = cv2.resize(frame, (400, 200))

    cv2.imshow("Original_video", frame)
    cv2.imshow("Resized_video", resized)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
