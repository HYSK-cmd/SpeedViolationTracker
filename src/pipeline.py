import os
import cv2
import numpy as np

from src.trapezoid_drawer import get_first_frame, Trapezoid
from src.video_speed_detector import VideoDetection
from src.livestream_speed_detector import LiveStreamDetection
import requests

def run_video(args, config):
    first_frame = get_first_frame(os.path.join("assets/videos", args.source_path))
    trapezoid = Trapezoid(first_frame)
    roi = trapezoid.get_source_roi_points()
    video = VideoDetection(
        vid_path=args.source_path,
        output_vid=args.output_video,
        model=args.model,
        roi=roi,
        config=config)
    video.detect()

def run_livestream(args, config):
    server = args.source_path
    res = requests.get(f"{server}/get_first_frame")
    img = np.frombuffer(res.content, np.uint8)
    first_frame = cv2.imdecode(img, cv2.IMREAD_COLOR)

    trapezoid = Trapezoid(first_frame)
    roi = trapezoid.get_source_roi_points()
    livestream = LiveStreamDetection(
        stream_url=args.source_path,
        output_vid=args.output_video,
        model=args.model,
        roi=roi,
        config=config,
    )
    livestream.detect()