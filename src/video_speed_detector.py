import os
import cv2
import numpy as np
from src.trapezoid_drawer import ROI
from src.base_detector import BaseDetector

class VideoDetection(BaseDetector):
    def __init__(self, vid_path: str, output_vid: str | None, model: str, roi: ROI, config: dict):
        source_path = os.path.join("assets/videos", vid_path)
        super().__init__(source_path=source_path, model=model, roi=roi, config=config, output_vid=output_vid)

        # Save the annotated result to outputs/videos/ (instead of the per-session log
        # folder) so it lands in a predictable, easy-to-find location.
        if output_vid:
            out_dir = os.path.abspath(os.path.join("outputs", "videos"))
            os.makedirs(out_dir, exist_ok=True)
            self.output_video = os.path.join(out_dir, output_vid)
