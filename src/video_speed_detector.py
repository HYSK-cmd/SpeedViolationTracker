import os
import cv2
import math
import logging
import numpy as np
from ultralytics import YOLO
from collections import defaultdict, deque

class VideoDetection:
    def __init__(self, vid_path, output_vid, model, roi, config):
        self.video = os.path.join("assets/videos", vid_path)
        self.model = YOLO(os.path.join('../Yolo-Models', model))
        self.output_video = os.path.join("outputs/videos", output_vid) if output_vid else None

        # video output type
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        # inference hyperparameters
        self.conf_threshold = config["conf_threshold"]
        self.iou_threshold = config["iou_threshold"]

        # speed limit
        self.speed_limit = config["SPEED_LIMIT"]

        # keep track of each frame
        self.frame_id = 0

        # convert source_roi to numpy array
        self.source = np.array(roi.points, dtype=np.float32)

        # real-world distance
        # WIDTH: real-world distance across the road
        # HEIGHT: real-world distance between upper and lower base of roi
        # currently used for testing speed estimation and will be replaced for livestream
        self.real_w, self.real_h = roi.real_w, roi.real_h

        # pixel height of the upper and the lower base of ROI
        self.upper_base = max(roi.points[0][1], roi.points[1][1])
        self.lower_base = min(roi.points[2][1], roi.points[3][1])

        # cam_frame
        self.frame_w = None
        self.frame_h = None
        self.fps = None

        # colors
        self.line_color = config["colors"]["LINE_COLOR"]
        self.text_color = config["colors"]["TEXT_COLOR"]
        self.box_color = config["colors"]["BOX_COLOR"]
        self.center_color = config["colors"]["CENTER_COLOR"]
        self.overlay_color = config["colors"]["OVERLAY_COLOR"]
        self.trapezoid_color = config["colors"]["TRAPEZOID_COLOR"]
        self.alpha = config["alpha"]

        # styles
        self.font_scale = config["font_scale"]
        self.thickness = config["thickness"]

        # memory
        self.track_memory = {}
        self.speed_violators = {}

        # logs
        logging.basicConfig(level=logging.INFO, filename=os.path.abspath(config["log_file"]))
        self.save_speeding_cars = os.path.abspath(config["save_speeding_cars_path"])

    # perspective transform requires source trapezoid and bird eye's view matrix
    def _get_perspective_trans(self, source_scaled) -> np.ndarray:
        target = np.array([
            [0, 0],
            [self.real_w - 1, 0],
            [self.real_w - 1, self.real_h - 1],
            [0, self.real_h - 1],
        ], dtype=np.float32)
        mat = cv2.getPerspectiveTransform(source_scaled, target)
        return mat

    # get bottom center points
    @staticmethod
    def _transform_points(points: np.ndarray, mat) -> np.ndarray:
        points = points.reshape(-1, 1, 2).astype(np.float32)
        transformed_points = cv2.perspectiveTransform(points, mat).reshape(-1, 2)
        return transformed_points

    @staticmethod
    def read_frame(cap):
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            yield frame

    def _calculate_inv_scale(self, clean_frame, x1, y1, x2, y2):
        inv_scale_x = self.frame_w / 1280
        inv_scale_y = self.frame_h / 720
        ix1 = int(x1 * inv_scale_x)
        iy1 = int(y1 * inv_scale_y)
        ix2 = int(x2 * inv_scale_x)
        iy2 = int(y2 * inv_scale_y)
        car_img = clean_frame[iy1:iy2, ix1:ix2]
        h = car_img.shape[0]
        return car_img[int(h*0.75):, :]

    def _check_speeding(self, track_id, speed, most_predicted_class, clean_frame, x1, y1, x2, y2):
        str_speed = f"{speed:.1f} km/h"
        self.speed_violators[track_id] = str_speed
        logging.warning(f"id={track_id} is speeding at {str_speed}")
        # make a filename
        filename = f"id_{track_id}_{most_predicted_class}.jpg"
        # inverse scale
        car_img = self._calculate_inv_scale(clean_frame, x1, y1, x2, y2)
        # save the photo of the speeding car
        cv2.imwrite(os.path.join(self.save_speeding_cars, filename), car_img)
        logging.info(f"id={track_id}, frame_A={self.track_memory[track_id]["A"]}, frame_B={self.track_memory[track_id]["B"]}, speed={speed:.1f} km/h")

    def detect(self):
        cap = cv2.VideoCapture(self.video)
        if not cap.isOpened():
            print("Unable to open video")
            return
        frame_generator = self.read_frame(cap)
        self.frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(cap.get(cv2.CAP_PROP_FPS))

        coordinates = defaultdict(lambda: deque(maxlen=self.fps))

        scale_x = 1280 / self.frame_w
        scale_y = 720 / self.frame_h
        source_scaled = (self.source * np.array([scale_x, scale_y])).astype(np.float32)
        upper_based_scaled = int(self.upper_base * scale_y)
        lower_based_scaled = int(self.lower_base * scale_y)
        target_mat = self._get_perspective_trans(source_scaled)
        video_output = None
        if self.output_video:
            video_output = cv2.VideoWriter(self.output_video, self.fourcc, self.fps, (1280, 720))

        while True:
            try:
                frame = next(frame_generator)
            except StopIteration:
                break
            # count each frame
            self.frame_id += 1
            clean_frame = frame.copy()
            frame = cv2.resize(frame, (1280, 720))

            overlay = frame.copy()
            cv2.fillPoly(overlay, [source_scaled.astype(np.int32)], color=self.trapezoid_color)
            cv2.addWeighted(overlay, self.alpha, frame, 1 - self.alpha, 0, frame)

            # model inference
            # persist=True keeps detected objects' id consistent across frames
            # verbose=False disables console logs for every frame
            results = self.model.track(
                frame,
                persist=True,
                verbose=False,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
            )[0]
            box_overlay = frame.copy()
            for box in results.boxes:
                # get classname for detected object
                cls = int(box.cls[0])
                # check if detected object is in a desired category
                # 2: car, 3: motorbike, 5: bus, 7: truck
                if cls not in [2, 3, 5, 7]:
                    continue
                # any objects other than ones above are filtered out
                if box.id is None:
                    continue
                # get each detected object's unique id
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

                points = self._transform_points(np.asarray([[cx, cy]]), target_mat)
                _, y = points[0]
                coordinates[track_id].append(y)
                speed = 0.0
                if len(coordinates[track_id]) > int(self.fps / 2):
                    coord_start = coordinates[track_id][0]
                    coord_end = coordinates[track_id][-1]
                    dist = abs(coord_start - coord_end)
                    time_ = len(coordinates[track_id]) / self.fps
                    speed = dist / time_ * 3.6  # km/h

                # detected car must have an initialized track entry
                if track_id in self.track_memory:
                    cross_line = self.track_memory[track_id]["cross_line"]
                    if cross_line is not None:
                        if self.track_memory[track_id]["A"] is None:
                            # check whether cars initially pass lower or upper base
                            if cross_line < upper_based_scaled <= cy:
                                self.track_memory[track_id]["A"] = ("upper", self.frame_id)
                            elif cy <= lower_based_scaled < cross_line:
                                self.track_memory[track_id]["A"] = ("lower", self.frame_id)
                        # check whether cars pass by the opposite end of roi
                        elif self.track_memory[track_id]["B"] is None:
                            first_line = self.track_memory[track_id]["A"][0]
                            if first_line == "upper" and cross_line < lower_based_scaled <= cy:
                                self.track_memory[track_id]["B"] = self.frame_id
                                self.track_memory[track_id]["speed"] = speed
                                # check if a detected car is speeding
                            elif first_line == "lower" and cy <= upper_based_scaled < cross_line:
                                self.track_memory[track_id]["B"] = self.frame_id
                                self.track_memory[track_id]["speed"] = speed
                                # check if a detected car is speeding

                # update cross_line
                self.track_memory[track_id]["cross_line"] = cy

                # draw bbox
                cv2.rectangle(box_overlay, (x1, y1), (x2, y2), self.box_color, -1)

                # display vehicle speed
                if is_inside_region and speed > 0.0:
                    if speed > self.speed_limit and track_id not in self.speed_violators:
                        self.speed_violators[track_id] = speed
                        logging.warning(f"id={track_id} is speeding at {speed:.1f} km/h")
                        self._check_speeding(track_id, speed, most_predicted_class, clean_frame, x1, y1, x2, y2)
                    color = (0, 0, 255) if track_id in self.speed_violators else (255, 255, 255)
                    cv2.putText(frame, f"{speed:.1f}km/h", (x1, y1 - 10),
                                cv2.FONT_HERSHEY_PLAIN, self.font_scale, color, self.thickness)

            # apply semi-transparent colored overlay over roi
            cv2.addWeighted(box_overlay, self.alpha, frame, 1 - self.alpha, 0, frame)

            # show each frame
            cv2.imshow("video", frame)

            # save frame if output_video exists
            if video_output is not None:
                video_output.write(frame)

            # press ESC to stop the video
            if cv2.waitKey(1) & 0xFF == 27:
                logging.info("Program paused")
                break

        # save video
        if video_output is not None:
            video_output.release()
            print("Video is successfully saved!")

        # close VideoCapture and window
        cap.release()
        cv2.destroyAllWindows()