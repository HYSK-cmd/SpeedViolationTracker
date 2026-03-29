# QUICKSTART
# 1) Install
```bash
git clone https://github.com/HYSK-cmd/SpeedViolaterDetector.git
python -m venv .venv

For MAC USER:
source .venv/bin/activate
For WINDOW USER:
.venv/Script/Activate.ps1

pip install -r requirements.txt
```
# 2) Run with default config
## Run video
```bash
python ./script.py --source video --source_path path/to/video.mp4 --model 'any yolo models(above v8)'
```
## Run livestream
```bash
python ./script.py --source livestream --save_video_path path/to/save/video.mp4 --model 'any yolo models(above v8)'
흠 라이브 스트림하고 그걸 비디오로 저장할까... 고민중
```
