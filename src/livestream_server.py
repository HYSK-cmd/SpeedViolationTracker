from flask import Flask, jsonify, Response
from picamera2 import Picamera2
import cv2
import threading
from ..config.loader import load_settings


class Camera:
    def __init__(self, config):
        self.picam2 = Picamera2()
        self.conf = self.picam2.create_video_configuration(
                        main={"size": (config["RES_W"], config["RES_H"]), "format": config["FORMAT"]}
                    )
        self.picam2.configure(self.conf)
        self.latest_frame = None
        self.lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None

    def start(self):
        try:
            self.picam2.start()
        except Exception as e:
            print(f"Picam2 Error: {e}")
            print("Background server terminating...")
            return
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._thread:
            self._thread.join()
        self.picam2.stop()

    def _capture_loop(self):
        while not self._stop.is_set():
            frame = self.picam2.capture_array()
            with self.lock:
                self.latest_frame = frame

    def get_frame(self):
        with self.lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None


def create_app():
    config = load_settings()
    app = Flask(__name__)
    cam = Camera(config)
    cam.start()

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

    @app.teardown_appcontext
    def shutdown(exception=None):
        print("Picam2 stopping...")
        cam.stop()
        print("Background server terminating...")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host='0.0.0.0', port=5000, threaded=True)
