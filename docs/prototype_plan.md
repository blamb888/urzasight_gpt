# Prototype Plan

## Goal

Build toward a manga-reading assistant that can see the current panel, answer a short voice request, and speak back concise reading help.

## Current Cleanup Scope

- Preserve `app_gpt.py` and `index_gpt.html` as the old browser/Tesseract reference.
- Do not expand the Tesseract, manga-ocr, or local CV path.
- Add simple Ubuntu camera scripts for the next hardware prototype.
- Document the native ChatGPT benchmark and hardware assumptions.

## Prototype Stages

### Stage 0: Native ChatGPT Benchmark

Use a phone mounted near eye level with native ChatGPT voice/camera support and AirPods. Measure whether the product idea feels useful before building the custom stack.

Primary questions:

- Can a mounted camera reliably see manga text at normal reading distance?
- Is voice interaction socially and ergonomically acceptable?
- How often does the assistant need a fresh image?
- What answer length is useful while reading?

### Stage 1: USB Camera Glasses Rig

Use an Ubuntu laptop as the host and a lightweight USB camera on glasses or a head strap. Validate camera stability, focus distance, lighting, and capture quality.

Local scripts:

- `scripts/list_cameras.sh`
- `scripts/preview_camera.sh`
- `scripts/capture_frame.py`

### Stage 2: Snapshot Flow

Capture a still frame on demand and send it to a vision-capable model. The first API version should favor a simple request/response loop over continuous video.

Expected flow:

1. Voice trigger or keyboard hotkey.
2. Capture one frame.
3. Submit image plus instruction prompt.
4. Speak a short response.
5. Save optional debug artifacts locally.

### Stage 3: Urzasight App

Wrap the snapshot flow in a small local app with hardware controls, prompt presets, transcript history, and privacy-friendly capture handling.

## Non-Goals For Now

- New OCR models.
- New OpenAI or Anthropic integration code.
- Real-time video streaming to APIs.
- Complex UI redesign.
- Production packaging.
