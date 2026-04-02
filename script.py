import argparse
from config.loader import load_settings
from src.pipeline import run_video, run_livestream

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
        required=True,
        help="Path to the output video file",
        type=str,
    )
    parser.add_argument(
        "--model",
        choices=["yolov8n.pt", "yolov8l.pt", "yolo11x.pt", "yolo26n.pt"],
        required=True,
        help="Path to the YOLOv8 model",
        type=str,
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    print(f"Source: {args.source}, Source_Path: {args.source_path}, Video_Output_Path: {args.output_video}, Model: {args.model}")
    config = load_settings()
    print(f"Settings: {config}")

    # choose video or livestream
    match args.source:
        case "video":
            run_video(args, config)
        case "livestream":
            run_livestream(args, config)

if __name__ == "__main__":
    main()