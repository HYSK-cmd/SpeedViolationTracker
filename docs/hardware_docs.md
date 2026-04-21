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
