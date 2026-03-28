import cv2
import math
import torch
import os
import copy
import logging
from ultralytics import YOLO

class Video_Dets:
    def __init__(self, vid_path, model, device, config):
        self.video = os.path.join("videos", vid_path)
        self.model = YOLO(os.path.join('../Yolo-Models', model))
        self.device = device

        # configs
        self.line_y1 = config["lines"]["line_A"][1]
        self.line_y2 = config["lines"]["line_B"][1]

        self.line_A = [x for x in config["lines"]["line_A"]]
        self.line_B = [y for y in config["lines"]["line_B"]]

        self.conf_threshold = config["conf_threshold"]
        self.real_dist_m = config["REAL_DIST_M"]
        self.speed_limit = config["SPEED_LIMIT"]

        self.frame_id = 0
        self.cnt = 0

        # colors
        self.line_color = config["colors"]["LINE_COLOR"]
        self.text_color = config["colors"]["TEXT_COLOR"]
        self.box_color = config["colors"]["BOX_COLOR"]
        self.overlay_color = config["colors"]["OVERLAY_COLOR"]

        # memory
        self.track_memory = {}
        self.speed_violators = {}

        # logs
        logging.basicConfig(level=logging.INFO, filename=os.path.abspath(config["log_file"]))

    def detect(self):
        cap = cv2.VideoCapture(self.video)
        fps = cap.get(cv2.CAP_PROP_FPS)
        print("FPS:", fps)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        '''
        mask
        line
        '''
        # fill detected objects
        # alpha = self.config["alpha"]

        # start video detection
        while True:
            ret, frame = cap.read()
            self.frame_id += 1
            if not ret:
                logging.info("Video ended")
                break

            results = self.model.track(frame, persist=True, verbose=False)[0]
            # persist=True keeps detected objects' id consistent across frames
            # verbose=False disables console logs for every frame

            cv2.line(frame, (self.line_A[0], self.line_A[1]), (self.line_A[2], self.line_A[3]), self.line_color, 2)
            # cv2.putText(frame, "Line A", (self.line_A[0], self.line_y1-12),
            #             cv2.FONT_HERSHEY_PLAIN, 3, self.config["colors"]["LINE_COLOR"], 2)
            cv2.putText(frame, "Line A", (self.line_A[0], self.line_y1 - 12),
                        cv2.FONT_HERSHEY_PLAIN, 1, self.text_color, 2)
            cv2.line(frame, (self.line_B[0], self.line_B[1]), (self.line_B[2], self.line_B[3]), self.line_color, 2)
            cv2.putText(frame, "Line B", (self.line_B[0], self.line_y2-12),
                        cv2.FONT_HERSHEY_PLAIN, 1, self.text_color, 2)

            for box in results.boxes:
                cls = int(box.cls[0])
                # check if detected object is in a desired category
                # 2: car, 3: motorbike, 5: bus, 7: truck
                if cls not in [2, 3, 5, 7]:
                    continue

                if box.id is None:
                    continue

                # bbox
                x1, y1, x2, y2 = box.xyxy[0]
                x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])

                # fill detected objects with color
                overlay = frame.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), self.box_color, -1)


                # confidence
                conf = math.ceil(box.conf[0] * 100) / 100

                # attach id to each detected object
                track_id = int(box.id[0])

                # find the center of detected object
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                cv2.circle(frame, (cx, cy), 3, self.line_color, -1)

                # initialize track entry
                if track_id not in self.track_memory and conf >= self.conf_threshold:
                    self.track_memory[track_id] = {
                        "A": None,
                        "B": None,
                        "speed": None,
                        "cross_line": None,
                    }

                if track_id in self.track_memory:
                    cross_line = self.track_memory[track_id]["cross_line"]

                    # line A
                    if cross_line is not None and self.track_memory[track_id]["A"] is None:
                        if cross_line < self.line_y1 <= cy:
                            self.track_memory[track_id]["A"] = self.frame_id

                    # line B
                    # detected objects must have valid A
                    if cross_line is not None and self.track_memory[track_id]["A"] is not None and self.track_memory[track_id]["B"] is None:
                        if cross_line < self.line_y2 <= cy:
                            self.track_memory[track_id]["B"] = self.frame_id
                            # calculate detected car's current speed
                            t1 = self.track_memory[track_id]["A"]
                            t2 = self.track_memory[track_id]["B"]
                            # frame difference over video fps to find the real-time difference
                            t = (t2 - t1) / fps
                            if t > 0:
                                speed = (self.real_dist_m / t) * 3.6
                                self.track_memory[track_id]["speed"] = speed
                                # check if a detected car is violating the speed constraint
                                if speed > self.speed_limit:
                                    if track_id not in self.speed_violators:
                                        str_speed = f"{speed:.1f} km/h"
                                        self.speed_violators[track_id] = str_speed
                                        logging.warning(f"id={track_id} is speeding at {str_speed}")
                                logging.info(f"id={track_id}, frame_A={self.track_memory[track_id]["A"]}, frame_B={self.track_memory[track_id]["B"]}, cross_line={cross_line}, speed={speed:.1f} km/h")
                    # update cross_line
                    self.track_memory[track_id]["cross_line"] = cy

                # draw box for detected objects
                cv2.rectangle(frame, (x1, y1), (x2, y2), self.box_color, 2)
                if track_id in self.track_memory:
                    car_speed = self.track_memory[track_id]["speed"]
                    if car_speed is not None:
                        str_speed = f"{car_speed}km/h"
                        if track_id not in self.speed_violators:
                            cv2.putText(frame, str_speed, (x1, y1 - 10), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)
                        else:
                            cv2.putText(frame, str_speed, (x1, y1 - 10), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)

            cv2.imshow("Video", frame)
            # press ESC to stop the video
            if cv2.waitKey(0) & 0xFF == 27:
                logging.info("Program paused")
                break

        print(self.speed_violators)
        cap.release()
        cv2.destroyAllWindows()