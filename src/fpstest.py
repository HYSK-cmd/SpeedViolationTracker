from flask import Flask, jsonify, Response
from picamera2 import Picamera2
import cv2
import threading

# FLASK for server, jsonify and Response for streaming/image response with json
# cv2 -> OpenCV
# threading for background threading

app = Flask(__name__)

# lock is necessary because of capture and get threads
latest_frame = None
lock = threading.Lock()

# pi camera setting, 1280 * 720
# format is RGB888 for now.
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "RGB888"}
)
picam2.configure(config)
picam2.start()

# A loop that captures frame
# Constantly updates the frame
# DO NOT use Queue due to latency issue
# This part might needs to be updated since the detection program uses queue
def capture_loop():
    global latest_frame
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR) # have to double check on this code, as video seems bluey
        with lock:
            latest_frame = frame

# thread for capturing, always capturing on separate thread
t = threading.Thread(target=capture_loop, daemon=True)
t.start()

# returning copy due to lock
def get_frame():
    with lock:
        return latest_frame.copy() if latest_frame is not None else None

# This is the part for ROI, where the first frame is needed.
# Incode it to JPEG, 50 is quality of that first frame (0: worst to 100: best)
@app.get("/get_first_frame")
def first_frame():
    frame = get_frame()
    _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
    return Response(buf.tobytes(), mimetype='image/jpeg')

# health check for server testing
@app.get("/health")
def health():
    return jsonify({"status": "ok"})

# livestreaming API
# similar to first_frame(), but keeps sending data
# inside yield is the MJPEG format
@app.get("/livestream")
def livestream():
    def generate():
        while True:
            frame = get_frame()
            if frame is None:
                continue
            _, buf = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' +
                buf.tobytes() +
                b'\r\n'
            )
    return Response( # Response from flask. streaming response
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# http info
def run():
    app.run(host="0.0.0.0", port=5000, threaded=True)

if __name__ == "__main__":
    run()