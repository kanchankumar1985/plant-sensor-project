#!/bin/bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if [ -d ".venv" ]; then
  source .venv/bin/activate
elif [ -d "venv" ]; then
  source venv/bin/activate
elif [ -d "../.venv" ]; then
  source ../.venv/bin/activate
elif [ -d "../venv" ]; then
  source ../venv/bin/activate
fi

SD_ROOT="/Volumes/SD-128GB/PlantMonitor"

if [ -d "$SD_ROOT" ] && [ -w "$SD_ROOT" ]; then
  export IMAGES_DIR="${IMAGES_DIR:-$SD_ROOT/images}"
  export VIDEOS_DIR="${VIDEOS_DIR:-$SD_ROOT/videos}"
  export LOGS_DIR="${LOGS_DIR:-$SD_ROOT/logs}"
else
  export IMAGES_DIR="${IMAGES_DIR:-$(pwd)/images}"
  export VIDEOS_DIR="${VIDEOS_DIR:-$(pwd)/videos}"
  export LOGS_DIR="${LOGS_DIR:-$(pwd)/logs}"
fi

mkdir -p "$IMAGES_DIR" "$VIDEOS_DIR" "$LOGS_DIR"

python3 vlm_worker.py
