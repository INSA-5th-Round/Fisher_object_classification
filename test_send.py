import requests

with open("frame_0.jpg", "rb") as image:

    files = {
        "image": ("frame.jpg", image, "image/jpeg")
    }

    response = requests.post(
        "http://127.0.0.1:5000/detect",
        files=files
    )

print("Status:", response.status_code)
print("Server:", response.text)
