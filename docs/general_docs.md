# Plans
## Software
### Key Updates
    - built a trapezoid drawer tool to extract coordinates
    - created docs to record necessary updates
    - developed speed estimation function
    - finished utils.py and video_speed_detector.py
    - created structure.md
    - created and orginized the general structure
### To-Dos
    - learn OCR to capture speeding cars' plate number (tentative)
    - learn Flask and JavaScript to create a backend server for launching a UI web
    - will add all testing videos in .gitignore 
    - Test the video with video taken from raspberry pi camera 
    - rename all videos
    - 연속된 프레임을 계속 찍어서 best frame을 추출?? -미계획-
    - change logs, output videos filenames to "%Y-%m-%d" or "%Y-%m-%d %H:%M or "%Y-%m-%d_%H-%M-%S"
        - logs structure in a tree form
```
i.e)
└───logs
    └───speeding_cars
        └───"%Y-%m-%d"
             └───"%Y-%m-%d_%H-%M-%S"
                  ├─── video
                  │   └─── *.mp4, *.webm 
                  ├─── *.png/jpg/jpeg
                  └─── *.log
```

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