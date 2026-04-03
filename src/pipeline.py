import os
from src.trapezoid_drawer import get_first_frame, Trapezoid
from src.video_speed_detector import VideoDetection

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
    pass