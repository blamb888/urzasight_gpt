#!/usr/bin/env bash
set -euo pipefail

DEVICE="${1:-/dev/video0}"
SIZE="${2:-1920x1080}"
FORMAT="${3:-mjpeg}"
FPS="${4:-30}"

if [ ! -e "$DEVICE" ]; then
  echo "Device not found: $DEVICE" >&2
  echo "Run: bash scripts/list_cameras.sh" >&2
  exit 1
fi

if ! command -v ffplay >/dev/null 2>&1; then
  echo "ffplay not found. Install it with:" >&2
  echo "  sudo apt-get update && sudo apt-get install -y ffmpeg" >&2
  exit 1
fi

exec ffplay \
  -hide_banner \
  -f v4l2 \
  -input_format "$FORMAT" \
  -framerate "$FPS" \
  -video_size "$SIZE" \
  "$DEVICE"
