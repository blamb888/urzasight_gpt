#!/usr/bin/env python3
"""Capture one frame from a Linux video device into captures/."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture one frame from a /dev/videoN device."
    )
    parser.add_argument("--device", default="/dev/video0", help="Camera device path.")
    parser.add_argument("--width", type=int, default=1280, help="Requested frame width.")
    parser.add_argument("--height", type=int, default=720, help="Requested frame height.")
    parser.add_argument(
        "--output-dir", default="captures", help="Directory for captured images."
    )
    parser.add_argument("--name", default="", help="Optional output filename.")
    return parser.parse_args()


def device_index(device: str) -> int | str:
    prefix = "/dev/video"
    if device.startswith(prefix):
        suffix = device.removeprefix(prefix)
        if suffix.isdigit():
            return int(suffix)
    return device


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(device_index(args.device), cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"Could not open camera device: {args.device}")
        return 1

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    ok, frame = cap.read()
    cap.release()

    if not ok or frame is None:
        print(f"Could not capture a frame from: {args.device}")
        return 1

    filename = args.name or f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    output_path = output_dir / filename

    if not cv2.imwrite(str(output_path), frame):
        print(f"Could not write capture: {output_path}")
        return 1

    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
