import os
from supervision.assets import VideoAssets, download_assets

os.chdir("../assets")
if not os.path.exists("videos"):
    os.makedirs("videos")
os.chdir("videos")
download_assets(VideoAssets.VEHICLES)