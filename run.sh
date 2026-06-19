#!/usr/bin/env bash
#
# This is a script for the whole setup and execution
# Usage:
#   ./run.sh                # start on http://127.0.0.1:5000 (local only)
#   HOST=0.0.0.0 ./run.sh   # also reachable from other devices on the LAN

set -euo pipefail

# always run from the root dir
cd "$(dirname "$0")"

VENV_DIR=".venv"
MODELS_DIR="../Yolo-Models"
HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5000}"

# create a virtual env if not set up yet
if [ ! -d "$VENV_DIR" ]; then
    echo "[setup] creating virtual environment in $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
fi

# activate
source "$VENV_DIR/bin/activate"

# install or update dependencies
echo "[setup] installing dependencies from requirements.txt ..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# sanity-check YOLO models
if [ ! -d "$MODELS_DIR" ]; then
    echo "[warning] '$MODELS_DIR' not found."
    echo "          Put your YOLO weight files (e.g. yolov8n.pt) in a 'Yolo-Models'"
    echo "          folder NEXT TO this project folder. Detection will fail without them."
else
    echo "[setup] using models from $MODELS_DIR:"
    ls "$MODELS_DIR"/*.pt 2>/dev/null || echo "          (no .pt files found in $MODELS_DIR)"
fi

# start the server
echo ""
echo "[run] starting server on http://$HOST:$PORT  (Ctrl+C to stop)"
echo ""
FLASK_RUN_HOST="$HOST" FLASK_RUN_PORT="$PORT" python app.py
