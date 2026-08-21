#!/bin/bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

with_frontend="${WITH_FRONTEND:-true}"
with_vlm_worker="${WITH_VLM_WORKER:-true}"
with_db="${WITH_DB:-true}"

if [ "$with_db" = "true" ]; then
  if command -v docker >/dev/null 2>&1; then
    if docker info >/dev/null 2>&1; then
      docker compose -f docker-compose.yml up -d
    else
      echo "Docker is installed but not running; skipping DB startup"
    fi
  else
    echo "Docker not found; skipping DB startup"
  fi
fi

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

pids=()
cleanup() {
  for pid in "${pids[@]}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
}
trap cleanup EXIT INT TERM

uvicorn app:app --port "${PORT:-8000}" &
pids+=("$!")

python3 serial_unified_listener.py &
pids+=("$!")

if [ "$with_vlm_worker" = "true" ]; then
  python3 vlm_worker.py &
  pids+=("$!")
fi

if [ "$with_frontend" = "true" ]; then
  if command -v npm >/dev/null 2>&1; then
    (cd ../frontend && npm run dev) &
    pids+=("$!")
  else
    echo "npm not found; skipping frontend"
  fi
fi

wait
