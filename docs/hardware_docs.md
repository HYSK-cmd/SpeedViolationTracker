# 04-03-2026
## Initial Hardware Setup (Raspberry Pi 5 + Camera Module)

### Components:
- Raspberry Pi 5
- Arducam Camera Module (IMX708)
- MicroSD Card (Raspberry Pi OS)
- Power Supply (5.1V 5A)
- CSI Camera Cable (default + UC-376 tested)
- Power Bank (Energizer Ultimate, 4.5V & 5A for fast-charging)
- Raspberry Pi 5 Cooler & Case
- Raspberry Pi Mouse

### Additional Tools:
- SD card reader for Pi OS

### Raspberry Pi Setup:
- Installed Raspberry Pi OS using Raspberry Pi Imager
    - Set up the customization of OS in order to connect wifi for Pi
- Updated Software & Driver Update
    - command: sudo apt update && sudo apt full-upgrade -y
- Enabled SSH for remote access
    - Used Windows PowerShell
    - command: ssh username@IP : connecting pi with laptop
    - command: sudo poweroff : For safe power off of pi
- Enabled VNC for GUI-based control
    - Used RealVNC Viewer
 
### Camera Installation:
- Connected camera via CSI port (CAM0)
- Tested both default cable and UC-376 cable
- Ensured correct cable orientation (metal contacts facing board)

### Indoor Camera Testing:
- Verified camera functionality using rpicam
    - command: rpicam-vid -t 5000 -o test.mp4 --width 1920 --height 1080 --framerate 30 (5 seconds, resolution: 1920*1080, fps: 30)
 
# 04-05-2026
## Outdoor Raspberry Pi & PiCamera Testing 

### Testing SSH connection with mobile Hotspot:
- Established SSH connection from laptop to Raspberry Pi
- Recorded the new IP address of Raspberry Pi
  - Command: arp -a
  - Command:
      1..50 | ForEach-Object {
        if (Test-Connection -ComputerName ("First_7_Digits_of_IP." + $_) -Count 1 -Quiet){
          "First_7_Digits_of_IP.$_ is up"
        }
    }

### Setup Environment:
- Used mobile hotspot for network connection with laptop
- Positioned Raspberry Pi on a side of pedestrian road
- Powered Pi using portable power bank (Energizer Ultimate)
- Recorded video footages of the road
    - command: rpicam-vid -t 5000 -o test.mp4 --width 1920 --height 1080 --framerate 30 (5 seconds, resolution: 1920*1080, fps: 30)

### Data Transfer:
- command: scp username@IP:/home/username/test_outdoor.mp4 .

# 04-07-2026
## Testing flask and HTTP server for livestreaming on Raspberry Pi
- Set up a Python virtual environment for flask testing
    - Command: python3 -m venv venv
    - Command: source venv/bin/activate
    - Command: pip install flask
- Verified basic Flask HTTP server functionality
    - Ran a simple Flask program (`Hello, World!`)
    - Confirmed access via browser: `http://127.0.0.1:5000`
- Tested Raspberry Pi camera using Python code
    - Successfully captured a frame and saved as an image file
    - Verified camera access through `Picamera2`

# 04-18-2026
## Video Livestreaming on Raspberry Pi
### Flask + PiCamera2 Server Setup:
- Developed an initial Flask-based HTTP server for Raspberry Pi camera streaming
- Initialized the Pi Camera globally using Picamera2 to avoid repeatedly opening the camera
- Configured camera capture at 1920x1080 resolution using RGB888 format
- Converted captured frames from RGB to BGR for OpenCV compatibility

### Server Endpoints:
- Started the server on Raspberry Pi
    - Command: `python3 livestream_server.py`
- Verified server health check
    - URL: `http://192.168.12.144:5000/health`
- Implemented endpoint to capture a single frame from the camera
    - URL: `http://192.168.12.144:5000/get_first_frame`
- Implemented MJPEG livestream endpoint for continuous video streaming
    - URL: `http://192.168.12.144:5000/livestream`

### Livestream Testing:
- Tested video livestreaming from Raspberry Pi to laptop through the local network
- Successfully confirmed that the laptop could receive live camera frames from the Raspberry Pi
- Observed significantly low FPS when fetching the livestream on the laptop side
- Identified potential bottlenecks from high-resolution frame capture, JPEG encoding, network transfer, and laptop-side frame decoding

# 04-19-2026
## Video livestreaming Optimization and Speed Detection Program Integration Test
- Improved the Flask livestreaming server by moving camera capture into an independent background thread
- Used a shared `latest_frame` buffer protected by `threading.Lock`
- Reduced camera resolution from 1920x1080 to 1280x720 to improve streaming stability and reduce network/encoding load

### Testing Results:
- Successfully confirmed that the laptop could receive continuous video input from the Raspberry Pi
- Verified that `/get_first_frame` and `/livestream` worked with the updated threaded capture design
- Observed improved responsiveness compared to the initial livestream implementation

### Speed Detector Program Test:
- Tested the livestream input with the speed detector program on the laptop side
    - Command: python script.py --source livestream --source_path http://192.168.12.144:5000 --output_video output.mp4 --model yolov8n.pt
- Confirmed that the detector could receive frames from the Raspberry Pi stream
- Identified that further FPS optimization may be needed for smoother real-time detection
