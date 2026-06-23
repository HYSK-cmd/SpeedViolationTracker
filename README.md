# Speed Violation Tracker
End-to-end computer vision pipeline for vehicle speed violator detection from videos and livestreams

## Demo
![Demo](assets/gif/demo.gif)
## QUICKSTART
### 1) Install
The setup scripts will automatically set up everything!
macOS/Linux:
```bash
git clone https://github.com/HYSK-cmd/SpeedViolaterDetector.git
./run.sh 
```
Windows PowerShell:
```bash
git clone https://github.com/HYSK-cmd/SpeedViolaterDetector.git
./run.ps1
```

### Prerequisite: YOLO Models
Model weights are **not** included in the repo. Place your `.pt` files in a
`Yolo-Models/` folder next to the project folder:
```
<parent>/
├── SpeedViolaterDetector/
└── Yolo-Models/
    └── yolov8n.pt, yolov8l.pt, ...
```

### 1.5) Raspberry Pi Camera Setup
ㄴssh into your raspberry pi5
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-picamera2
```

### 2) Run with default config
#### Run video
```bash
python ./script.py --source video --source_path path/to/video.mp4 --output_video *.mp4 --model *.pt
```
#### Run livestream
```bash
flask run
python ./script.py --source livestream --source_path stream_url --output_video *.mp4 --model *.pt
```
### Run the Web App
`./run.sh` starts a web server — open it in a browser.
```bash
# local only
./run.sh

# share on the same Wi-Fi
HOST=0.0.0.0 ./run.sh
```
> `HOST=0.0.0.0 PORT=5001 ./run.sh`
> Set `FLASK_DEBUG=1` only while developing.

### Livestream Config
Set the Raspberry Pi camera server address in `config/settings.yaml`:
```yaml
STREAM_URL: "http://<pi-ip>:5000"
```
The Pi and the web server must be on the same network.

### Storage
Each run creates a session folder:
```
logs/speeding_cars/<YYYY-MM-DD>/<YYYY-MM-DD_HH-MM-SS>/
├── <session>.log            # run log
├── id_<id>_<class>.jpg      # captured speed violators (car/truck/motorcycle/bus)
└── video/                   # annotated output video (if "Save Video" is on)
```

### 3) Project Structure
```
Computer_Vision/
├───assets/
│   └───videos/
│       └───*.mp4
├───config/
│   ├───__init__.py
│   ├───loader.py
│   └───settings.yaml
├───docs/
│   ├───general_docs.md
│   ├───hardware_docs.md
│   ├───hardware_docs.md
│   └───structure.md
├───logs/
│   └───logs
│   └───speeding_cars
│       └───"%Y-%m-%d"
│            └───"%Y-%m-%d_%H-%M-%S"
│                 ├─── video
│                 │   └─── *.mp4, *.webm 
│                 ├─── *.png/jpg/jpeg
│                 └─── *.log
├───src/
│   ├───web/
│   │   ├───__init__.py
│   │   ├───routes.py
│   │   └───services.py
│   ├───__init__.py
│   ├───livestream_speed_detector.py
│   ├───pipeline.py
│   ├───utils.py
│   └───video_speed_detector.py
├───static/
│   ├───css/
│   │   └───style.css
│   └───js/
│       └───main.js
├───templates/
│   └───index.html
├───Yolo-Models/
│   └───*.pt
├───.gitignore
├───app.py
├───requirements.txt
└───script.py
```
