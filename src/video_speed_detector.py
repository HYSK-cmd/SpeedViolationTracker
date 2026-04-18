import os
import cv2
import numpy as np
from src.trapezoid_drawer import ROI
from src.base_detector import BaseDetector

class VideoDetection(BaseDetector):
    def __init__(self, vid_path: str, output_vid: str | None, model: str, roi: ROI, config: dict):
        super().__init__(model=model, roi=roi, config=config, output_vid=output_vid)
        self.video = os.path.join("assets/videos", vid_path)

    def _open_source(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self.video)
        assert cap.isOpened(), "Unable to open video"
        return cap

    @staticmethod
    def read_frame(cap: cv2.VideoCapture) -> np.ndarray:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            yield frame
