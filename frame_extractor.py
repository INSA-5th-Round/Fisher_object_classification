import cv2

# Open the video
cap = cv2.VideoCapture("test_frame2q.mp4")

count = 0

while True:
    # Take one frame from the video
    ret, frame = cap.read()

    # Stop when there are no more frames
    if not ret:
        break

    # Save every 30th frame as an image
    if count % 30 == 0:
        cv2.imwrite(f"frame_{count}.jpg", frame)
        print(f"Saved frame_{count}.jpg")

    count += 1

# Close the video
cap.release()

print("Finished. Total frames:", count)
