import os
import tqdm
from ultralytics.utils.downloads import safe_download
from huggingface_hub import hf_hub_download

# mkdir -p ../Yolo-Models
os.makedirs('../Yolo-Models', exist_ok=True)

# cd ./Yolo-Models
os.chdir("../Yolo-Models")
print(os.getcwd())

# download videos and models for testing
