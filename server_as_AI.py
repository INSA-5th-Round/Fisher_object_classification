from flask import Flask, request
import os
import time

app = Flask(__name__)

os.makedirs("received_frames", exist_ok=True)

@app.route("/detect", methods=["POST"])
def receive_image():

    image = request.files.get("image")

    if image is None:
        print("No image received")
        return "No image received", 400
    
    filename = f"frame_{time.time_ns()}.jpg"

    image.save(os.path.join("received_frames", filename))

    print("Saved:", filename)

    return "Image received successfully", 200


app.run(host="127.0.0.1", port=5000)