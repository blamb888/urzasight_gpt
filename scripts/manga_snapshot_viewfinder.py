#!/usr/bin/env python3
"""Local C922 viewfinder that saves snapshots without closing preview."""

from __future__ import annotations

import argparse
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Open a local manga viewfinder and capture stills on command."
    )
    parser.add_argument("--device", default="/dev/video2", help="Camera device path.")
    parser.add_argument("--width", type=int, default=1920, help="Requested frame width.")
    parser.add_argument("--height", type=int, default=1080, help="Requested frame height.")
    parser.add_argument(
        "--format",
        default="MJPG",
        help="Requested fourcc pixel format, for example MJPG or YUYV.",
    )
    parser.add_argument("--fps", type=float, default=30, help="Requested FPS.")
    parser.add_argument(
        "--output-dir", default="captures", help="Directory for captured images."
    )
    parser.add_argument(
        "--window-name", default="urzasight_gpt manga viewfinder", help="Preview title."
    )
    return parser.parse_args()


def device_index(device: str) -> int | str:
    prefix = "/dev/video"
    if device.startswith(prefix):
        suffix = device.removeprefix(prefix)
        if suffix.isdigit():
            return int(suffix)
    return device


def terminal_trigger_worker(triggers: "queue.Queue[str]") -> None:
    while True:
        line = sys.stdin.readline()
        if line == "":
            return
        triggers.put("capture")


def snapshot_path(output_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"manga_snapshot_{timestamp}.jpg"


def main() -> int:
    args = parse_args()
    try:
        import cv2
    except ImportError as exc:
        raise SystemExit(
            "Missing Python package: opencv-python\n"
            "Install it with: python3 -m pip install -r requirements_gpt.txt"
        ) from exc

    format_code = args.format[:4].upper()
    if len(format_code) != 4:
        print(f"Pixel format must be a four-character code: {args.format}")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(device_index(args.device), cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"Could not open camera device: {args.device}")
        return 1

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*format_code))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    if args.fps > 0:
        cap.set(cv2.CAP_PROP_FPS, args.fps)

    triggers: "queue.Queue[str]" = queue.Queue()
    threading.Thread(target=terminal_trigger_worker, args=(triggers,), daemon=True).start()

    print("Viewfinder open.")
    print("Capture: press Enter in this terminal, or Enter/Space/S in the preview window.")
    print("Quit: press Q or Esc in the preview window, or Ctrl+C in this terminal.")

    saved_count = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                print(f"Could not read a frame from: {args.device}")
                return 1

            display = frame.copy()
            cv2.putText(
                display,
                "Enter/Space/S: capture  Q/Esc: quit",
                (24, 42),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow(args.window_name, display)

            key = cv2.waitKey(1) & 0xFF
            should_capture = key in (10, 13, 32, ord("s"), ord("S"))
            should_quit = key in (27, ord("q"), ord("Q"))

            while not triggers.empty():
                triggers.get_nowait()
                should_capture = True

            if should_capture:
                path = snapshot_path(output_dir)
                if cv2.imwrite(str(path), frame):
                    saved_count += 1
                    print(f"Saved: {path}")
                else:
                    print(f"Could not write capture: {path}")

            if should_quit:
                break
    except KeyboardInterrupt:
        print()
    finally:
        cap.release()
        cv2.destroyAllWindows()

    print(f"Viewfinder closed. Snapshots saved: {saved_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
