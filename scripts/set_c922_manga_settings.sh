#!/usr/bin/env bash
set -euo pipefail

DEVICE="${1:-/dev/video2}"

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

echo "Applying C922 manga test settings to $DEVICE"
v4l2-ctl -d "$DEVICE" --set-ctrl=focus_automatic_continuous=0
v4l2-ctl -d "$DEVICE" --set-ctrl=focus_absolute=60
v4l2-ctl -d "$DEVICE" --set-ctrl=sharpness=180
v4l2-ctl -d "$DEVICE" --set-ctrl=power_line_frequency=1

echo
echo "Current C922 focus/sharpness/power-line controls:"
v4l2-ctl -d "$DEVICE" --list-ctrls | grep -E "focus_automatic_continuous|focus_absolute|sharpness|power_line_frequency" || true
