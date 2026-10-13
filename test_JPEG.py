#This converts an OpenCV image like png into a JPEG representation.then send for processing
import cv2

image = cv2.imread("frame.png")

ok, jpg = cv2.imencode(
    ".jpg",
    image,
    [int(cv2.IMWRITE_JPEG_QUALITY), 85]
)   #JPEG in memory

if ok:
    print("JPEG encoding successful")
else:
    print("JPEG encoding failed")

# changing the encoded JPEG into bytes
data = jpg.tobytes()
print("Conversion to bytes successful")
print("Data type:", type(data))
print("Size:", len(data), "bytes")





