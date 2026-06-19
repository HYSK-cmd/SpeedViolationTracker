# Plans
## Software
### Key Updates
    - Built a trapezoid drawer tool to extract coordinates
    - Created docs to record necessary updates
    - Developed speed estimation function
    - Finished utils.py and video_speed_detector.py
    - Created structure.md
    - Created and orginized the general structure
    - Created livestream background server that will be deployed on raspberry pi
    - Completed the pipeline for video and livestream (livestream will be debugged and tested by April 27th)
    - Changed logs, output videos filenames to "%Y-%m-%d" or "%Y-%m-%d %H:%M or "%Y-%m-%d_%H-%M-%S"
    - Renamed all videos
### To-Dos
    - Will add all testing videos in .gitignore 
    - Test the video with video taken from raspberry pi camera

## Hardware
### Key Updates
    - Successfully completed initial hardware setup using Raspberry Pi 5 and Arducam IMX708 camera
    - Established remote access via SSH (PowerShell) and GUI control via VNC
    - Verified stable connectivity using both local WiFi and mobile hotspot environments
    - Implemented camera functionality using rpicam tools (image + video capture)
    - Conducted indoor and outdoor camera testing
    - Validated file transfer workflow from Raspberry Pi to laptop using SCP
    - Confirmed feasibility of recording and handling high-resolution video data (1080p @ 30fps)
    - Observed impact of bitrate and resolution on video file size and quality
### To-Dos
    - Implement real-time video streaming from Raspberry Pi to laptop
    - Construct HTTP server
    - Optimize camera parameters (focus, exposure, bitrate, resolution)