import cv2
import queue
import threading
import numpy as np
from src.trapezoid_drawer import ROI
from src.base_detector import BaseDetector

class LiveStreamDetection(BaseDetector):
    def __init__(self, stream_url: str, model: str, roi: ROI, config: dict, output_vid: str | None = None):
        super().__init__(model=model, roi=roi, config=config, output_vid=output_vid)
        self.stream_url = stream_url
        self.frame_queue = queue.Queue()
        self._stop = threading.Event()

    def _open_source(self) -> cv2.VideoCapture:
        cap = cv2.VideoCapture(self.stream_url)
        assert cap.isOpened(), "Unable to connect to livestream"
        return cap

    def read_frame(self, cap: cv2.VideoCapture):
        reader = threading.Thread(target=self._frame_reader, args=(cap,), daemon=True)
        reader.start()
        while not self._stop.is_set():
            try:
                frame = self.frame_queue.get(timeout=1)
                yield frame
            except queue.Empty:
                continue

    def _on_detect_end(self, cap: cv2.VideoCapture, video_output: cv2.VideoWriter | None):
        self._stop.set()
        super()._on_detect_end(cap, video_output)