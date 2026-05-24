#!/usr/bin/env bash
set -euo pipefail

missing=0

if ! command -v lsusb >/dev/null 2>&1; then
  echo "Missing required tool: lsusb" >&2
  echo "Install it with: sudo apt-get update && sudo apt-get install -y usbutils" >&2
  missing=1
fi

if ! command -v v4l2-ctl >/dev/null 2>&1; then
  echo "Missing required tool: v4l2-ctl" >&2
  echo "Install it with: sudo apt-get update && sudo apt-get install -y v4l-utils" >&2
  missing=1
fi

if [ "$missing" -ne 0 ]; then
  exit 1
fi

echo "USB devices:"
lsusb || true

echo
echo "V4L2 devices:"
v4l2-ctl --list-devices || true

echo
echo "/dev/v4l/by-id paths:"
if [ -d /dev/v4l/by-id ]; then
  find /dev/v4l/by-id -maxdepth 1 -type l -print | sort | while read -r path; do
    printf "%s -> %s\n" "$path" "$(readlink -f "$path")"
  done
else
  echo "No /dev/v4l/by-id directory found."
fi

echo
echo "Capture node formats:"
shopt -s nullglob
devices=(/dev/video*)
if [ "${#devices[@]}" -eq 0 ]; then
  echo "No /dev/video* devices found."
  exit 0
fi

for dev in "${devices[@]}"; do
  [ -e "$dev" ] || continue
  caps="$(v4l2-ctl -d "$dev" --all 2>/dev/null || true)"
  if ! printf "%s\n" "$caps" | grep -Eq "Video Capture|Video Capture Multiplanar"; then
    continue
  fi

  echo
  echo "== $dev =="
  v4l2-ctl -d "$dev" --info || true
  echo
  v4l2-ctl --list-formats-ext -d "$dev" || true
done
