#!/usr/bin/env bash
set -euo pipefail

DEVICE="${1:-/dev/video2}"
OUTPUT_DIR="captures"
FOCUS_VALUES=(0 20 40 60 80 100 120 140 160)

if [ ! -e "$DEVICE" ]; then
  echo "Device not found: $DEVICE" >&2
  echo "Run: bash scripts/list_cameras.sh" >&2
  exit 1
fi

if ! command -v v4l2-ctl >/dev/null 2>&1; then
  echo "v4l2-ctl not found. Install it with:" >&2
  echo "  sudo apt-get update && sudo apt-get install -y v4l-utils" >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "Disabling continuous autofocus on $DEVICE"
v4l2-ctl -d "$DEVICE" --set-ctrl=focus_automatic_continuous=0

for focus in "${FOCUS_VALUES[@]}"; do
  filename="c922_focus_${focus}.jpg"
  echo
  echo "Focus $focus -> $OUTPUT_DIR/$filename"
  v4l2-ctl -d "$DEVICE" --set-ctrl=focus_absolute="$focus"
  sleep 1
  python3 scripts/capture_frame.py \
    --device "$DEVICE" \
    --width 1920 \
    --height 1080 \
    --format MJPG \
    --warmup-frames 10 \
    --output-dir "$OUTPUT_DIR" \
    --name "$filename"
done
