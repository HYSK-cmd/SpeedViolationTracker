import os
import argparse
from src.utils import get_first_frame, Trapezoid
from config.loader import load_settings
from src.video_speed_detector import VideoDetection

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Vehicle Speed Estimation using Inference and Supervision"
    )
    parser.add_argument(
        "--source",
        choices=["video", "livestream"],
        required=True,
        help="Choose the source",
        type=str,
    )
    parser.add_argument(
        "--source_path",
        required=True,
        help="Path to the source",
        type=str,
    )
    parser.add_argument(
        "--output_video",
        required=False,
        help="Path to the output video file",
        type=str,
    )
    parser.add_argument(
        "--model",
        choices=["yolov8n.pt", "yolov8l.pt", "yolo26n.pt", "yolo11x.pt"],
        required=True,
        help="Path to the YOLOv8 model",
        type=str,
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    print(f"Source: {args.source}, Source_Path: {args.source_path}, Video_Output_Path: {args.output_video}, Model: {args.model}")
    config = load_settings()
    print(f"Settings: {config}")

    match args.source:
        case "video":
            first_frame = get_first_frame(os.path.join("assets/videos", args.source_path))
            trapezoid = Trapezoid(first_frame)
            roi = trapezoid.get_source_roi_points()
            video = VideoDetection(vid_path=args.source_path, output_vid=args.output_video, model=args.model, roi=roi, config=config)
            video.detect()
        case "livestream":
            pass
