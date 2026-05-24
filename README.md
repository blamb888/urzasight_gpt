# urzasight_gpt

Experimental manga-reading assistant prototype.

This repo currently keeps the original browser/Tesseract prototype for reference while the next direction is explored: a lightweight glasses-mounted USB camera connected to an Ubuntu laptop, with AirPods used for microphone and audio output. The future Urzasight app is expected to use snapshot-based vision APIs rather than expanding the old OCR/CV path.

## Current Tracks

### 1. Native ChatGPT Headstrap Benchmark

Before building more software, benchmark the simplest version of the idea: phone mounted near eye level, native ChatGPT voice/camera flow, and AirPods for audio. This gives a baseline for comfort, latency, reading accuracy, and interaction style.

See [docs/benchmark_headstrap_test.md](docs/benchmark_headstrap_test.md).

### 2. USB Camera Glasses Prototype

The next hardware prototype uses:

- Lightweight USB camera mounted to glasses or a head strap
- Ubuntu laptop as the host
- AirPods for microphone and audio
- Simple local scripts for camera discovery, preview, and still capture

See [docs/camera_hardware_notes.md](docs/camera_hardware_notes.md).

### 3. Future API-Based Urzasight App

The intended app flow is:

1. Capture a high-resolution snapshot from the head-mounted camera.
2. Send the image to an OpenAI or Anthropic vision API.
3. Ask for manga-specific reading help: transcription, furigana/readings, translation, grammar, and tone.
4. Return a short spoken answer through AirPods.

No new OCR models or API integrations are added in this cleanup pass.

## Reference App

The existing FastAPI app remains available as a reference:

- `app_gpt.py`
- `index_gpt.html`

Run it with:

```bash
uvicorn app_gpt:app --reload --host 0.0.0.0 --port 8000
```

Install Python dependencies with:

```bash
pip install -r requirements_gpt.txt
```

System-level Tesseract/Japanese language packs are still required only for the old reference OCR flow.

## USB Camera Test Commands

List connected cameras and supported formats:

```bash
bash scripts/list_cameras.sh
```

Preview a camera:

```bash
bash scripts/preview_camera.sh /dev/video0
```

Capture one frame:

```bash
python3 scripts/capture_frame.py --device /dev/video0
```

Captured frames are saved under `captures/`, which is ignored by Git.
