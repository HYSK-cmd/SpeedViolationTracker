import cv2
from src.trapezoid_drawer import ROI
from src.base_detector import BaseDetector

class LiveStreamDetection(BaseDetector):
    def __init__(self, stream_url: str, model: str, roi: ROI, config: dict, output_vid: str | None = None):
        super().__init__(source_path=stream_url, model=model, roi=roi, config=config, output_vid=output_vid)

    def read_frame(self, cap: cv2.VideoCapture):
        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            yield frame
