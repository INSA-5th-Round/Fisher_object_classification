import cv2

cap = cv2.VideoCapture("test_frame2.mp4")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # ROI coordinates
    x1= 80
    x2= 400
    y1 = 0
    y2 = 350


    preview = frame.copy()

    # Draw rectangle around the ROI
    cv2.rectangle(
        preview,
        (x1, y1),
        (x2,y2),
        (0, 255, 0),
        2
    )

    cv2.imshow("CCTV Preview", preview)

    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
