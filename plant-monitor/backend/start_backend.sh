#!/bin/bash
export IMAGES_DIR=/Volumes/SD-128GB/PlantMonitor/images
export VIDEOS_DIR=/Volumes/SD-128GB/PlantMonitor/videos
uvicorn app:app --reload --port 8000
