#!/usr/bin/env python3
"""Capture one frame from a Linux video device into captures/."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture one frame from a /dev/videoN device."
    )
    parser.add_argument("--device", default="/dev/video0", help="Camera device path.")
    parser.add_argument("--width", type=int, default=1280, help="Requested frame width.")
    parser.add_argument("--height", type=int, default=720, help="Requested frame height.")
    parser.add_argument(
        "--format",
        default="MJPG",
        help="Requested fourcc pixel format, for example MJPG or YUYV.",
    )
    parser.add_argument(
        "--warmup-frames",
        type=int,
        default=5,
        help="Frames to discard before saving the still image.",
    )
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
    try:
        import cv2
    except ImportError as exc:
        raise SystemExit(
            "Missing Python package: opencv-python\n"
            "Install it with: python3 -m pip install -r requirements_gpt.txt"
        ) from exc

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(device_index(args.device), cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"Could not open camera device: {args.device}")
        return 1

    if args.format:
        fourcc = cv2.VideoWriter_fourcc(*args.format[:4].upper())
        cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    ok = False
    frame = None
    for _ in range(max(args.warmup_frames, 0) + 1):
        ok, frame = cap.read()

    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    if not ok or frame is None:
        print(f"Could not capture a frame from: {args.device}")
        return 1

    filename = args.name or f"frame_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    output_path = output_dir / filename

    if not cv2.imwrite(str(output_path), frame):
        print(f"Could not write capture: {output_path}")
        return 1

    print(f"Saved: {output_path}")
    print(f"Requested: {args.width}x{args.height} {args.format.upper()}")
    print(f"Actual: {actual_width}x{actual_height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
