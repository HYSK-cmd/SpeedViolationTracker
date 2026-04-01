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