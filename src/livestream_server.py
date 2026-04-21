from flask import Flask, jsonify, Response
from picamera2 import Picamera2
import cv2
import threading
from ..config.loader import load_settings

config = load_settings()
app = Flask(__name__)

class Camera:
    def __init__(self, config):
        self.picam2 = Picamera2()
        self.conf = self.picam2.create_video_configuration(
                        main={"size": (config["RES_W"], config["RES_H"]), "format": config["FORMAT"]}
                    )
        self.picam2.configure(self.conf)
        self.latest_frame = None
        self.lock = threading.Lock()

    def start(self):
        try:
            self.picam2.start()
        except Exception as e:
            print("Picam2 Error {e}")

    def capture_loop(self):
        while True:
            frame = self.picam2.capture_array()
            with self.lock:
                self.latest_frame = frame

    def get_frame(self):
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None


cam = Camera(config)
cam.start()
cam.app.run(host="0.0.0.0", port=5000)

@app.get("/get_first_frame")
def first_frame():
    frame = cam.get_frame()
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 100])
    return Response(buf.tobytes(), mimetype='image/jpeg')

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/livestream")
def livestream():
    def generate():
        while True:
            frame = cam.get_frame()
            if frame is None:
                continue
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                buf.tobytes() +
                b'\r\n'
            )
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')