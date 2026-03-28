import os
import argparse
from src.utils import get_first_frame, filter_image
from config.loader import load_settings
from src.detection_for_video import Video_Dets

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
        "--model",
        choices=["yolov8n.pt", "yolov8l.pt"],
        required=True,
        help="Path to the YOLOv8 model",
        type=str,
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    print(f"Source: {args.source}, Source_Path: {args.source_path} Model: {args.model}")
    config = load_settings()
    print(f"Settings: {config}")

    match args.source:
        case "video":
            first_frame = get_first_frame(os.path.join("assets/videos", args.source_path))
            filtered_image = filter_image(first_frame)
            #filter_image(args.source_path)
            exit(0)
            video = Video_Dets(vid_path=args.source_path, model=args.model, config=config)
            video.detect()
        case "livestream":
            pass
