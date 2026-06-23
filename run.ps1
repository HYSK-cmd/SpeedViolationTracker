# This is a script for the whole setup and execution (Windows / PowerShell)
# Usage:
#   .\run.ps1                          # start on http://127.0.0.1:5000 (local only)
#   $env:HOST="0.0.0.0"; .\run.ps1     # also reachable from other devices on the LAN

$ErrorActionPreference = "Stop"

# always run from the root dir
Set-Location -Path $PSScriptRoot

$VenvDir = ".venv"
$ModelsDir = "..\Yolo-Models"
$HostAddr = if ($env:HOST) { $env:HOST } else { "127.0.0.1" }
$Port = if ($env:PORT) { $env:PORT } else { "5000" }

# find a python launcher
$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $PythonCmd) {
    throw "Python not found on PATH. Install Python and try again."
}

# create a virtual env if not set up yet
if (-not (Test-Path $VenvDir)) {
    Write-Host "[setup] creating virtual environment in $VenvDir ..."
    & $PythonCmd.Source -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { throw "venv creation failed" }
}

# activate
& "$VenvDir\Scripts\Activate.ps1"

# install or update dependencies
Write-Host "[setup] installing dependencies from requirements.txt ..."
python -m pip install --quiet --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip upgrade failed" }
python -m pip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "dependency install failed" }

# sanity-check YOLO models
if (-not (Test-Path $ModelsDir)) {
    Write-Host "[warning] '$ModelsDir' not found."
    Write-Host "          Put your YOLO weight files (e.g. yolov8n.pt) in a 'Yolo-Models'"
    Write-Host "          folder NEXT TO this project folder. Detection will fail without them."
} else {
    Write-Host "[setup] using models from ${ModelsDir}:"
    $models = Get-ChildItem -Path $ModelsDir -Filter *.pt -ErrorAction SilentlyContinue
    if ($models) {
        $models | ForEach-Object { Write-Host "          $($_.Name)" }
    } else {
        Write-Host "          (no .pt files found in $ModelsDir)"
    }
}

# start the server
Write-Host ""
Write-Host "[run] starting server on http://${HostAddr}:${Port}  (Ctrl+C to stop)"
Write-Host ""
$env:FLASK_RUN_HOST = $HostAddr
$env:FLASK_RUN_PORT = $Port
python app.py
