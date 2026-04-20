# 04-20-2026
## Threading and Livestreaming Implementation (Raspberry Pi Camera + Flask Server)

### Goal:
- Build a lightweight livestreaming server on Raspberry Pi
- Continuously capture frames from Pi Camera Module
- Captures the first frame and transmit it in JPEG format

### Main Idea:
- Used a background thread to continuously capture the most recent camera frame
- Stored only the latest frame in a shared buffer
- Served the frame through Flask endpoints using HTTP

### Threading Structure:
- Created a global frame buffer:
  - `latest_frame = None`
- Added a thread lock:
  - `lock = threading.Lock()`
- Implemented a background capture loop:
  - continuously reads frames from PiCamera
  - converts frame format when needed
  - overwrites `latest_frame` with the newest frame

### Reason for Threading:
- Without threading, the fps of livestreaming video was significantly low.
- Flask server must stay responsive to incoming HTTP requests
- Camera capture must keep running continuously in parallel

### Camera Configuration:
- Used `Picamera2` for Raspberry Pi camera access
- Configured video mode:
  - resolution: `1280 x 720`
  - format: `RGB888`

### Livestreaming Endpoints:
- `/get_first_frame`
  - returns one JPEG image
  - used for grabbing the first frame for ROI/trapezoid drawing
- `/livestream`
  - returns an MJPEG stream
  - continuously sends JPEG-encoded frames over HTTP

### Testing / Observations:
- Confirmed that the Flask server can provide both first-frame image and live stream
- Verified that livestream URL can be accessed over the network
- Blue-tinted stream was observed during testing
  - likely caused by RGB/BGR color channel mismatch between `Picamera2` and OpenCV
  - color conversion logic needs additional verification

### Related Commands / Execution:
- Run Flask livestream server on Raspberry Pi
  - command: `python3 livestream_server.py`
- Example server address
  - `http://<pi_ip>:5000/health`
  - `http://<pi_ip>:5000/get_first_frame`
  - `http://<pi_ip>:5000/livestream`

### Next Steps:
- Verify correct color conversion between `Picamera2` output and OpenCV pipeline
- Connect livestream URL to `livestream_speed_detector`
- Measure latency and adjust frame handling if needed
