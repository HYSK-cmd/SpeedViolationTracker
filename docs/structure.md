```
Computer_Vision/
├───assets/
│   ├───gif/
│   │   └───demo.gif
│   └───videos/
│       └───*.mp4
├───config/
│   ├───__init__.py
│   ├───loader.py
│   └───settings.yaml
├───docs/
│   ├───general_docs.md
│   ├───hardware_docs.md
│   ├───software_docs.md
│   └───structure.md
├───download/
│   ├───__init__.py
│   └───download.py
├───logs/
│   ├───info.log
│   └───speeding_cars/
│       └───"%Y-%m-%d"/
│            └───"%Y-%m-%d_%H-%M-%S"/
│                 ├───video/
│                 │   └───*.mp4, *.webm
│                 ├───*.png/jpg/jpeg
│                 └───*.log
├───outputs/
│   └───videos/
│       └───*.mp4
├───src/
│   ├───web/
│   │   ├───__init__.py
│   │   └───routes.py
│   ├───__init__.py
│   ├───base_detector.py
│   ├───livestream_server.py
│   ├───livestream_speed_detector.py
│   ├───pipeline.py
│   ├───testing_license_plates.ipynb
│   ├───trapezoid_drawer.py
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
├───README.md
├───requirements.txt
└───script.py
```