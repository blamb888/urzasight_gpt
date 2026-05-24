# C922 Camera Test Notes

This repo is temporarily using a Logitech C922 Pro Stream Webcam as the reliable fallback prototype camera while the Waveshare OS05A10 path is investigated. The goal is a conversational manga-reading assistant, not a flat document-scanning rig.

## Detected Device

Ubuntu currently reports:

```text
C922 Pro Stream Webcam (usb-0000:00:14.0-2):
  /dev/video2
  /dev/video3
  /dev/media1
```

The likely capture node is `/dev/video2`. Confirm on each boot with:

```bash
bash scripts/list_cameras.sh
```

Prefer `/dev/v4l/by-id/...` symlinks when you need a stable path across reboots.

## Preferred Modes

Preferred manga test mode:

```text
MJPG 1920x1080 @ 30fps
```

Fallback modes:

```text
MJPG 1280x720 @ 30fps
MJPG 1280x720 @ 60fps
```

YUYV modes may be present, but MJPG is preferred for this C922 test harness because it supports the desired high-resolution frame rate.

## Preferred Physical Setup

Use the C922 tripod-mounted and forward-facing, with the reader holding the manga naturally in front of the camera at a comfortable reading distance. This is closer to the eventual glasses-camera use case than a top-down desk scanner.

Current best baseline:

```text
focus_absolute=40
MJPG 1920x1080 @ 30fps
sharpness=180
power_line_frequency=1
```

Use `power_line_frequency=1` for Tokyo/Japan East 50Hz lighting. Early focus sweep results made `40` and `60` the best candidates, with `40` currently preferred and `60` kept as a backup.

## Manual Focus Procedure

1. Apply the starting manga settings:

   ```bash
   bash scripts/set_c922_manga_settings.sh /dev/video2
   ```

2. Preview the camera:

   ```bash
   bash scripts/preview_camera.sh /dev/video2 1920x1080 mjpeg 30
   ```

3. Run a focus sweep:

   ```bash
   bash scripts/c922_focus_sweep.sh /dev/video2
   ```

4. Compare the generated files under `captures/`:

   ```text
   captures/c922_focus_0.jpg
   captures/c922_focus_20.jpg
   ...
   captures/c922_focus_160.jpg
   ```

The current starting point disables continuous autofocus, sets manual focus to `40`, sharpness to `180`, and power-line frequency to `1` for 50Hz Tokyo/Japan East lighting.

## Manga Capture Tips

- Use bright, even light.
- Hold the manga naturally in front of the forward-facing camera.
- Keep the manga page steady for 1-2 seconds before capture.
- Avoid fingers covering the text.
- Hold one page or panel centered in frame rather than an entire spread.
- Let focus settle before capturing.
- Compare the focus sweep images at full size.

Top-down capture can still be useful as an optional alternative for controlled comparison shots, but it is not the main workflow for this prototype.
