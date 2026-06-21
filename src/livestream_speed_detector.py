import cv2
import time
import math
import logging
import threading
import numpy as np
from collections import defaultdict, deque
from src.trapezoid_drawer import ROI
from src.base_detector import BaseDetector


class _FrameGrabber:
    """Background thread: continuously reads from stream, keeps only the latest frame."""
    def __init__(self, cap: cv2.VideoCapture):
        self._cap = cap
        self._frame = None
        self._lock = threading.Lock()
        self._stopped = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        while not self._stopped:
            ret, frame = self._cap.read()
            if not ret:
                continue
            with self._lock:
                self._frame = frame

    def read(self):
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def stop(self):
        self._stopped = True
        self._thread.join(timeout=3)


class LiveStreamDetection(BaseDetector):
    def __init__(self, stream_url: str, model: str, roi: ROI, config: dict, output_vid: str | None = None):
        super().__init__(source_path=stream_url, model=model, roi=roi, config=config, output_vid=output_vid)

    def detect(self, stop_event: threading.Event | None = None):
        cap = self._open_source()

        self.frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30

        video_output = None
        if self.output_video:
            video_output = cv2.VideoWriter(self.output_video, self.fourcc, self.fps, (1280, 720))

        scale_x = 1280 / self.frame_w
        scale_y = 720 / self.frame_h
        source_scaled = (self.source * np.array([scale_x, scale_y])).astype(np.float32)
        upper_scaled = int(self.upper_base * scale_y)
        lower_scaled = int(self.lower_base * scale_y)
        target_mat = self._get_perspective_trans(source_scaled)

        grabber = _FrameGrabber(cap)

        # inference thread -> main thread: latest detection results
        _draw_data = []
        _draw_lock = threading.Lock()
        _stopped = threading.Event()

        # tracking state (inference thread only)
        coordinates = defaultdict(lambda: deque(maxlen=self.fps))

        def inference_loop():
            while not _stopped.is_set():
                raw = grabber.read()
                if raw is None:
                    continue

                self.frame_id += 1
                clean_frame = raw
                frame = cv2.resize(raw, (1280, 720))

                results = self.model.track(
                    frame, persist=True, verbose=False,
                    conf=self.conf_threshold, iou=self.iou_threshold,
                )[0]

                frame_dets = []

                for box in results.boxes:
                    cls = int(box.cls[0])
                    if cls not in [2, 3, 5, 7]:
                        continue
                    if box.id is None:
                        continue
                    track_id = int(box.id[0])

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = math.ceil(box.conf[0] * 100) / 100

                    cx, cy = (x1 + x2) // 2, y2
                    is_inside = cv2.pointPolygonTest(source_scaled.astype(np.int32), (cx, cy), False) >= 0

                    pts = self._transform_points(np.asarray([[cx, cy]]), target_mat)
                    _, y = pts[0]

                    # use real timestamps instead of frame count for accurate speed with frame skipping
                    now = time.time()
                    coordinates[track_id].append((y, now))
                    speed = 0.0

                    if len(coordinates[track_id]) > int(self.fps / 2):
                        y_start, t_start = coordinates[track_id][0]
                        y_end, t_end = coordinates[track_id][-1]
                        elapsed = t_end - t_start
                        if elapsed > 0:
                            speed = abs(y_start - y_end) / elapsed * 3.6

                    if track_id not in self.track_memory and conf >= self.conf_threshold:
                        self.track_memory[track_id] = {
                            "A": None, "B": None, "speed": None,
                            "cross_line": None, "classification": {}
                        }

                    classname = self.model.names[cls]
                    candidates = self.track_memory[track_id]["classification"]
                    candidates[classname] = candidates.get(classname, 0) + 1
                    most_predicted = max(candidates, key=candidates.get)

                    # cross-line detection for A/B speed measurement
                    if track_id in self.track_memory:
                        cl = self.track_memory[track_id]["cross_line"]
                        if cl is not None:
                            if self.track_memory[track_id]["A"] is None:
                                if cl < upper_scaled <= cy:
                                    self.track_memory[track_id]["A"] = ("upper", self.frame_id)
                                elif cy <= lower_scaled < cl:
                                    self.track_memory[track_id]["A"] = ("lower", self.frame_id)
                            elif self.track_memory[track_id]["B"] is None:
                                first = self.track_memory[track_id]["A"][0]
                                if first == "upper" and cl < lower_scaled <= cy:
                                    self.track_memory[track_id]["B"] = self.frame_id
                                    self.track_memory[track_id]["speed"] = speed
                                elif first == "lower" and cy <= upper_scaled < cl:
                                    self.track_memory[track_id]["B"] = self.frame_id
                                    self.track_memory[track_id]["speed"] = speed

                    self.track_memory[track_id]["cross_line"] = cy

                    is_violator = track_id in self.speed_violators
                    if is_inside and speed > 0.0:
                        if speed > self.speed_limit and not is_violator:
                            self.speed_violators[track_id] = speed
                            logging.warning(f"id={track_id} is speeding at {speed:.1f} km/h")
                            self._capture_vehicle(track_id, speed, most_predicted, clean_frame, x1, y1, x2, y2)
                            is_violator = True

                    frame_dets.append({
                        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                        "cls_name": classname, "conf": conf,
                        "cx": cx, "cy": cy,
                        "speed": speed, "is_inside": is_inside,
                        "is_violator": is_violator,
                    })

                with _draw_lock:
                    _draw_data.clear()
                    _draw_data.extend(frame_dets)

        # start inference in background thread
        thread = threading.Thread(target=inference_loop, daemon=True)
        thread.start()

        # main thread: display at stream FPS, overlay latest inference results
        frame_interval = 1.0 / self.fps
        while True:
            if stop_event is not None and stop_event.is_set():
                logging.info("Livestream stopped")
                break

            raw = grabber.read()
            if raw is None:
                continue

            # without an interactive window cv2.waitKey() no longer paces the loop,
            # so throttle to the stream FPS to avoid a busy-spin and duplicate writes
            if not self.display:
                time.sleep(frame_interval)

            frame = cv2.resize(raw, (1280, 720))

            # draw ROI
            overlay = frame.copy()
            cv2.fillPoly(overlay, [source_scaled.astype(np.int32)], color=self.trapezoid_color)
            cv2.addWeighted(overlay, self.alpha, frame, 1 - self.alpha, 0, frame)

            # draw latest detection results
            with _draw_lock:
                dets = list(_draw_data)

            box_overlay = frame.copy()
            for d in dets:
                x1, y1, x2, y2 = d["x1"], d["y1"], d["x2"], d["y2"]
                cv2.putText(frame, f"{d['cls_name']}: {d['conf']}", (x1, y1 - 40),
                            cv2.FONT_HERSHEY_PLAIN, self.font_scale, self.text_color, self.thickness)
                cv2.circle(frame, (d["cx"], d["cy"]), 3, self.center_color, -1)
                cv2.rectangle(box_overlay, (x1, y1), (x2, y2), self.box_color, -1)

                if d["is_inside"] and d["speed"] > 0.0:
                    color = (0, 0, 255) if d["is_violator"] else (255, 255, 255)
                    cv2.putText(frame, f"{d['speed']:.1f}km/h", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_PLAIN, self.font_scale, color, self.thickness)

            cv2.addWeighted(box_overlay, self.alpha, frame, 1 - self.alpha, 0, frame)

            # push the annotated frame to the web live stream if a sink is attached
            if self.frame_sink is not None:
                self.frame_sink(frame)

            # preview only on the main thread (CLI); the web app runs in a worker thread
            if self.display:
                cv2.imshow("video", frame)
            if video_output is not None:
                video_output.write(frame)

            # stop on ESC (CLI preview) or when the web app signals via stop_event
            if self.display and cv2.waitKey(1) & 0xFF == 27:
                logging.info("Livestream stopped")
                break
            if stop_event is not None and stop_event.is_set():
                logging.info("Livestream stopped")
                break

        _stopped.set()
        grabber.stop()
        thread.join(timeout=3)
        self._on_detect_end(cap, video_output)
