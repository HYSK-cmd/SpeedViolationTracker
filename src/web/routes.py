import os
import cv2
import queue
import threading
import logging
from flask import Blueprint, render_template, request, jsonify, Response, current_app, send_file
from io import BytesIO

web_bp = Blueprint('web', __name__)

# SSE log broadcasting
log_queues = []
log_lock = threading.Lock()


class QueueHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        with log_lock:
            for q in log_queues:
                q.put(msg)


# attach handler to root logger so all logging.info/warning/error calls are captured
_handler = QueueHandler()
_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S'))
logging.getLogger().addHandler(_handler)
logging.getLogger().setLevel(logging.INFO)


@web_bp.route('/')
def index():
    return render_template('index.html')


@web_bp.route('/api/upload', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    file.save(save_path)
    logging.info(f"Uploaded: {file.filename}")
    return jsonify({'filename': file.filename})


@web_bp.route('/api/video/first-frame/<filename>')
def first_frame(filename):
    video_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    cap = cv2.VideoCapture(video_path)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return jsonify({'error': 'Cannot read video'}), 400
    _, buf = cv2.imencode('.jpg', frame)
    return send_file(BytesIO(buf.tobytes()), mimetype='image/jpeg')


@web_bp.route('/api/video/run', methods=['POST'])
def run_video():
    data = request.json
    filename = data.get('filename')
    output_video = data.get('output_video')
    model = data.get('model')
    roi_data = data.get('roi')
    if not filename or not roi_data:
        return jsonify({'error': 'Missing filename or ROI'}), 400

    def _run():
        from config.loader import load_settings
        from src.trapezoid_drawer import ROI
        from src.video_speed_detector import VideoDetection
        config = load_settings()
        roi = ROI(
            points=roi_data['points'],
            real_w=roi_data['real_w'],
            real_h=roi_data['real_h'],
        )
        logging.info(f"Starting video detection: {filename}")
        try:
            video = VideoDetection(
                vid_path=filename,
                output_vid=output_video,
                model=model,
                roi=roi,
                config=config,
            )
            video.detect()
            logging.info("Video detection completed")
        except Exception as e:
            logging.error(f"Detection error: {e}")

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({'message': 'Processing started'})


@web_bp.route('/api/livestream/start', methods=['POST'])
def start_livestream():
    logging.info("Livestream started")
    return jsonify({'message': 'Livestream started'})


@web_bp.route('/api/livestream/stop', methods=['POST'])
def stop_livestream():
    logging.info("Livestream stopped")
    return jsonify({'message': 'Livestream stopped'})


@web_bp.route('/api/logs/stream')
def stream_logs():
    q = queue.Queue()
    with log_lock:
        log_queues.append(q)

    def generate():
        try:
            while True:
                try:
                    msg = q.get(timeout=30)
                    yield f"data: {msg}\n\n"
                except queue.Empty:
                    yield "data: \n\n"
        finally:
            with log_lock:
                log_queues.remove(q)

    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
