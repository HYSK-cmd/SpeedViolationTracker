import argparse
import torch
from ultralytics import YOLO
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
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device Use: {"GPU" if device.type == "cuda" else "CPU"}")
    print(device)

    match args.source:
        case "video":
            video = Video_Dets(vid_path=args.source_path, model=args.model, device=device, config=config)
            video.detect()
        case "livestream":
            pass
