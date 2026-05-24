# Camera Hardware Notes

## Target Setup

- Lightweight USB camera mounted on glasses or a head strap.
- Ubuntu laptop as compute host.
- AirPods for microphone input and spoken output.
- Snapshot capture first, not continuous streaming.

## Camera Requirements

Prefer a camera with:

- UVC support so it appears as `/dev/videoN` on Linux.
- 1080p capture support.
- Manual or fixed focus that works at manga reading distance.
- Low weight and a cable that does not pull the frame out of position.
- Reasonable low-light performance under indoor lighting.

## Mounting Notes

The camera should be close to the reader's line of sight, but it does not need to be perfectly centered for the first benchmark. Stability matters more than elegance.

Things to test:

- Can the page stay in frame while reading normally?
- Does the cable tug when turning the head?
- Is the image sharp at normal book distance?
- Does glare from glossy pages make text unreadable?
- Does the mount stay comfortable for 20 minutes?

## Ubuntu Checks

List devices and formats:

```bash
bash scripts/list_cameras.sh
```

Preview a likely device:

```bash
bash scripts/preview_camera.sh /dev/video0
```

Capture a still:

```bash
python3 scripts/capture_frame.py --device /dev/video0
```

If `/dev/video0` is not the right camera, use the device reported by `list_cameras.sh`.

## AirPods Notes

Pair AirPods through the Ubuntu Bluetooth settings. For the prototype, keep audio simple:

- AirPods microphone for voice commands.
- AirPods output for spoken responses.
- Laptop keyboard fallback for capture trigger during debugging.
