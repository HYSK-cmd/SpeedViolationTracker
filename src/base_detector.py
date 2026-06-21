import os
import cv2
import math
import logging
import threading
import numpy as np
from ultralytics import YOLO
from datetime import datetime
from src.trapezoid_drawer import ROI
from collections import defaultdict, deque

class BaseDetector:
    def __init__(self, source_path: str, model: str, roi: ROI, config: dict, output_vid: str | None = None):
        self.source_path = source_path
        self.model = YOLO(os.path.join("../Yolo-Models", model))
        self.output_video = None

        # Live preview via cv2.imshow only works on the main thread (OpenCV HighGUI
        # requirement; on macOS calling it from a worker thread aborts the process with a
        # C++/NSException). The web app constructs detectors inside a Flask worker thread,
        # so disable the preview there; the CLI runs on the main thread and keeps it.
        self.display = threading.current_thread() is threading.main_thread()

        # Optional callable(frame) used to push annotated frames somewhere other than a
        # cv2 window (the web app sets this to stream frames to the browser as MJPEG).
        self.frame_sink = None

        # video output type
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        # inference hyperparameters
        self.conf_threshold = config["CONF_THRESHOLD"]
        self.iou_threshold = config["IOU_THRESHOLD"]

        # speed limit
        self.speed_limit = config["SPEED_LIMIT"]

        # keep track of each frame
        self.frame_id = 0

        # convert source_roi to numpy array
        self.source = np.array(roi.points, dtype=np.float32)

        # real-world distance
        self.real_w, self.real_h = roi.real_w, roi.real_h

        # pixel height of the upper and the lower base of ROI
        self.upper_base = max(roi.points[0][1], roi.points[1][1])
        self.lower_base = min(roi.points[2][1], roi.points[3][1])

        # cam_frame
        self.frame_w = None
        self.frame_h = None
        self.fps = None

        # colors
        self.line_color = config["COLORS"]["LINE_COLOR"]
        self.text_color = config["COLORS"]["TEXT_COLOR"]
        self.box_color = config["COLORS"]["BOX_COLOR"]
        self.center_color = config["COLORS"]["CENTER_COLOR"]
        self.overlay_color = config["COLORS"]["OVERLAY_COLOR"]
        self.trapezoid_color = config["COLORS"]["TRAPEZOID_COLOR"]
        self.alpha = config["ALPHA"]

        # styles
        self.font_scale = config["FONT_SCALE"]
        self.thickness = config["THICKNESS"]

        # memory
        self.track_memory = {}
        self.speed_violators = {}

        # logs
        now = datetime.now()
        date_dir = now.strftime("%Y-%m-%d")
        session_dir = now.strftime("%Y-%m-%d_%H-%M-%S")
        base_log_path = os.path.abspath(config["SAVE_SPEEDING_CARS_PATH"])
        self.session_path = os.path.join(base_log_path, date_dir, session_dir)
        self.save_speeding_cars = self.session_path
        self.video_output_dir = os.path.join(self.session_path, "video")
        os.makedirs(self.save_speeding_cars, exist_ok=True)
        os.makedirs(self.video_output_dir, exist_ok=True)

        # per-session log file named with the date format (e.g. 2025-04-04_06-18-00.log).
        # We attach a FileHandler directly instead of using logging.basicConfig(): in the
        # web process the root logger already has the SSE QueueHandler, so basicConfig()
        # is a no-op and the file would never be written. Any FileHandler left over from a
        # previous session in the same process is removed so each log file only holds its
        # own session.
        log_file = os.path.join(self.session_path, f"{session_dir}.log")
        root_logger = logging.getLogger()
        for handler in list(root_logger.handlers):
            if getattr(handler, "_session_handler", False):
                root_logger.removeHandler(handler)
                handler.close()
        file_handler = logging.FileHandler(log_file)
        file_handler._session_handler = True
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        )
        root_logger.addHandler(file_handler)
        root_logger.setLevel(logging.INFO)

        if output_vid:
            self.output_video = os.path.join(self.video_output_dir, output_vid)

    # perspective transform requires source trapezoid and bird eye's view matrix
    def _get_perspective_trans(self, source_scaled: np.ndarray) -> np.ndarray:
        target = np.array([
            [0, 0],
            [self.real_w - 1, 0],
            [self.real_w - 1, self.real_h - 1],
            [0, self.real_h - 1],
        ], dtype=np.float32)
        mat = cv2.getPerspectiveTransform(source_scaled, target)
        return mat

    @staticmethod
    # apply perspective transform matrix to given points
    def _transform_points(points: np.ndarray, mat: np.ndarray) -> np.ndarray:
        points = points.reshape(-1, 1, 2).astype(np.float32)
        transformed_points = cv2.perspectiveTransform(points, mat).reshape(-1, 2)
        return transformed_points

    # crop the lower quarter of the detected vehicle bbox scaled back to original res
    def _calculate_inv_scale(self, clean_frame: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> np.ndarray:
        inv_scale_x = self.frame_w / 1280
        inv_scale_y = self.frame_h / 720
        ix1 = int(x1 * inv_scale_x)
        iy1 = int(y1 * inv_scale_y)
        ix2 = int(x2 * inv_scale_x)
        iy2 = int(y2 * inv_scale_y)
        car_img = clean_frame[iy1:iy2, ix1:ix2]
        return car_img

    # capture speeding vehicles
    def _capture_vehicle_image(self, track_id: int, speed: float, most_predicted_class: str, clean_frame: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> None:
        str_speed = f"{speed:.1f} km/h"
        self.speed_violators[track_id] = str_speed
        logging.warning(f"id={track_id} is speeding at {str_speed}")
        filename = f"id_{track_id}_{most_predicted_class}.jpg"
        car_img = self._calculate_inv_scale(clean_frame, x1, y1, x2, y2)
        cv2.imwrite(os.path.join(self.save_speeding_cars, filename), car_img)
        logging.info(f"id={track_id}, frame_A={self.track_memory[track_id]["A"]}, frame_B={self.track_memory[track_id]["B"]}, speed={speed:.1f} km/h")

    # log and save photos of speeding vehicles
    def _capture_vehicle(self, track_id: int, speed: float, most_predicted_class: str, clean_frame: np.ndarray, x1: int, y1: int, x2: int, y2: int):
        self._capture_vehicle_image(track_id, speed, most_predicted_class, clean_frame, x1, y1, x2, y2)

    def _open_source(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self.source_path)
        assert cap.isOpened(), f"Unable to open source: {self.source_path}"
        return cap

    def read_frame(self, cap: cv2.VideoCapture):
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            yield frame

    # end detection program if interrupted or finished
    def _on_detect_end(self, cap: cv2.VideoCapture, video_output: cv2.VideoWriter):
        if video_output is not None:
            video_output.release()
            logging.info("Video is successfully saved!")
        cap.release()
        if self.display:
            cv2.destroyAllWindows()

    # main execution: frame reading, model inference, vehicle tracking, speed estimation
    def detect(self):
        cap = self._open_source()

        # set a frame generator
        frame_generator = self.read_frame(cap)

        # get original resolution and fps
        self.frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(cap.get(cv2.CAP_PROP_FPS))

        # total frame count for progress logging (0 if the source can't report it)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        next_progress = 10  # log progress every ~10%

        # if output video exists
        video_output = None
        if self.output_video:
            video_output = cv2.VideoWriter(self.output_video, self.fourcc, self.fps, (1280, 720))

        # store recent y-coords per track_id for speed estimation over each second
        coordinates = defaultdict(lambda: deque(maxlen=self.fps))

        # scale factors to map original frame coords to fixed res
        scale_x = 1280 / self.frame_w
        scale_y = 720 / self.frame_h
        source_scaled = (self.source * np.array([scale_x, scale_y])).astype(np.float32)

        # adjust to apply the proper scale factors
        upper_based_scaled = int(self.upper_base * scale_y)
        lower_based_scaled = int(self.lower_base * scale_y)
        target_mat = self._get_perspective_trans(source_scaled)

        while True:
            try:
                frame = next(frame_generator)
            except StopIteration:
                break

            self.frame_id += 1

            # log progress so the web log panel shows activity during long videos
            if total_frames > 0:
                pct = self.frame_id * 100 // total_frames
                if pct >= next_progress:
                    logging.info(f"Processing: {pct}% ({self.frame_id}/{total_frames} frames)")
                    next_progress += 10

            # keep the original frame to capture speeding vehicles' license plate
            clean_frame = frame

            # resize to a fixed res
            frame = cv2.resize(frame, (1280, 720))

            # draw a roi over video
            overlay = frame.copy()
            cv2.fillPoly(overlay, [source_scaled.astype(np.int32)], color=self.trapezoid_color)
            cv2.addWeighted(overlay, self.alpha, frame, 1 - self.alpha, 0, frame)

            # model inference
            results = self.model.track(
                frame,
                persist=True,
                verbose=False,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
            )[0]

            # copy the frame to draw a box for object detection
            box_overlay = frame.copy()

            # iterate over detected vehicles
            for box in results.boxes:
                cls = int(box.cls[0])
                # 2: car, 3: motorbike, 5: bus, 7: truck
                if cls not in [2, 3, 5, 7]:
                    continue
                if box.id is None:
                    continue
                track_id = int(box.id[0])

                # bbox
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                # confidence
                conf = math.ceil(box.conf[0] * 100) / 100

                # display classname and confidence value
                cv2.putText(frame, f"{self.model.names[cls]}: {conf}", (x1, y1 - 40),
                            cv2.FONT_HERSHEY_PLAIN, self.font_scale, self.text_color, self.thickness)

                # find the bottom center of detected cars
                cx, cy = (x1 + x2) // 2, y2
                is_inside_region = cv2.pointPolygonTest(source_scaled.astype(np.int32), (cx, cy), False) >= 0
                cv2.circle(frame, (cx, cy), 3, self.center_color, -1)

                # project bottom center point into real-world coords space via perspective transform
                points = self._transform_points(np.asarray([[cx, cy]]), target_mat)

                # extract y-axis
                _, y = points[0]

                # accumulate real-world y pos over frames
                coordinates[track_id].append(y)
                speed = 0.0

                # estimate speed
                if len(coordinates[track_id]) > int(self.fps / 2):
                    coord_start = coordinates[track_id][0]
                    coord_end = coordinates[track_id][-1]
                    dist = abs(coord_start - coord_end)
                    time_ = len(coordinates[track_id]) / self.fps
                    speed = dist / time_ * 3.6  # km/h

                # initialize track entry
                if track_id not in self.track_memory and conf >= self.conf_threshold:
                    self.track_memory[track_id] = {
                        "A": None,
                        "B": None,
                        "speed": None,
                        "cross_line": None,
                        "classification": {}
                    }

                # majority voting for stable class prediction per track
                classname = self.model.names[cls]
                candidates = self.track_memory[track_id]["classification"]
                candidates[classname] = candidates.get(classname, 0) + 1
                most_predicted_class = max(candidates, key=candidates.get)

                # detected car must have an initialized track entry
                if track_id in self.track_memory:
                    cross_line = self.track_memory[track_id]["cross_line"]
                    if cross_line is not None:
                        if self.track_memory[track_id]["A"] is None:
                            if cross_line < upper_based_scaled <= cy:
                                self.track_memory[track_id]["A"] = ("upper", self.frame_id)
                            elif cy <= lower_based_scaled < cross_line:
                                self.track_memory[track_id]["A"] = ("lower", self.frame_id)
                        elif self.track_memory[track_id]["B"] is None:
                            first_line = self.track_memory[track_id]["A"][0]
                            if first_line == "upper" and cross_line < lower_based_scaled <= cy:
                                self.track_memory[track_id]["B"] = self.frame_id
                                self.track_memory[track_id]["speed"] = speed
                            elif first_line == "lower" and cy <= upper_based_scaled < cross_line:
                                self.track_memory[track_id]["B"] = self.frame_id
                                self.track_memory[track_id]["speed"] = speed

                # update cross_line
                self.track_memory[track_id]["cross_line"] = cy

                # draw bbox
                cv2.rectangle(box_overlay, (x1, y1), (x2, y2), self.box_color, -1)

                # display vehicle speed
                if is_inside_region and speed > 0.0:
                    if speed > self.speed_limit and track_id not in self.speed_violators:
                        self.speed_violators[track_id] = speed
                        logging.warning(f"id={track_id} is speeding at {speed:.1f} km/h")
                        self._capture_vehicle(track_id, speed, most_predicted_class, clean_frame, x1, y1, x2, y2)
                    color = (0, 0, 255) if track_id in self.speed_violators else (255, 255, 255)
                    cv2.putText(frame, f"{speed:.1f}km/h", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_PLAIN, self.font_scale, color, self.thickness)

            # apply semi-transparent colored overlay over roi
            cv2.addWeighted(box_overlay, self.alpha, frame, 1 - self.alpha, 0, frame)

            # push the annotated frame to the web live stream if a sink is attached
            if self.frame_sink is not None:
                self.frame_sink(frame)

            # show each frame (preview only on the main thread; see __init__)
            if self.display:
                cv2.imshow("video", frame)

            # save frame if output_video exists
            if video_output is not None:
                video_output.write(frame)

            # press ESC to stop (interactive preview only)
            if self.display and cv2.waitKey(1) & 0xFF == 27:
                logging.info("Program paused")
                break

        self._on_detect_end(cap, video_output)
