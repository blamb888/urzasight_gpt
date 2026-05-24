#!/usr/bin/env bash
set -euo pipefail

if ! command -v v4l2-ctl >/dev/null 2>&1; then
  echo "v4l2-ctl not found. Installing v4l-utils with apt..."
  sudo apt-get update
  sudo apt-get install -y v4l-utils
fi

echo "Video devices:"
v4l2-ctl --list-devices || true

echo
echo "Device formats:"
for dev in /dev/video*; do
  [ -e "$dev" ] || continue
  echo
  echo "== $dev =="
  v4l2-ctl --device="$dev" --list-formats-ext || true
done
