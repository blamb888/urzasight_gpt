#!/usr/bin/env bash
set -euo pipefail

DEVICE="${1:-/dev/video2}"
WIDTH="${2:-1920}"
HEIGHT="${3:-1080}"
FORMAT="${4:-MJPG}"
FPS="${5:-30}"
OUTPUT_DIR="captures"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
FILENAME="manga_snapshot_${TIMESTAMP}.jpg"

mkdir -p "$OUTPUT_DIR"

output="$(
  python3 scripts/capture_frame.py \
    --device "$DEVICE" \
    --width "$WIDTH" \
    --height "$HEIGHT" \
    --format "$FORMAT" \
    --fps "$FPS" \
    --warmup-frames 10 \
    --output-dir "$OUTPUT_DIR" \
    --name "$FILENAME"
)"

printf "%s\n" "$output"
printf "Snapshot path: %s/%s\n" "$OUTPUT_DIR" "$FILENAME"
