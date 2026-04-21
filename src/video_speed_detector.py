import os
import cv2
import numpy as np
from src.trapezoid_drawer import ROI
from src.base_detector import BaseDetector

class VideoDetection(BaseDetector):
    def __init__(self, vid_path: str, output_vid: str | None, model: str, roi: ROI, config: dict):
        source_path = os.path.join("assets/videos", vid_path)
        super().__init__(source_path=source_path, model=model, roi=roi, config=config, output_vid=output_vid)
