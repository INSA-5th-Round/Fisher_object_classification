import cv2

cap = cv2.VideoCapture("test_frame.mp4")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Crop: y1:y2 (vertical area (Y)), x1:x2 (horizontal area (X))
    roi = frame[0:350, 80:400]

    cv2.imshow("Original", frame)
    cv2.imshow("ROI / Cropped", roi)

    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()