import os
from supervision.assets import VideoAssets, download_assets

SAVE_VIDEO_PATH = os.path.join(".", "assets", "videos")
os.chdir(SAVE_VIDEO_PATH)
download_assets(VideoAssets.VEHICLES)
download_assets(VideoAssets.VEHICLES_2)