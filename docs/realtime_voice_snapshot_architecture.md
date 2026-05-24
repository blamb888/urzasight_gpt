# Realtime Voice + Snapshot Architecture

Urzasight's MVP is a voice-first manga tutor. The user wears AirPods, keeps a local camera preview open, speaks naturally, and gets a short spoken answer when they ask about the visible manga.

## Why Voice + Snapshot

The goal is conversational reading help, not document scanning and not continuous surveillance of the camera feed. The camera is a local viewfinder until the user asks for help. At that moment, Urzasight captures one high-resolution still and sends only that still plus the spoken question to the model.

This keeps the prototype close to the eventual glasses-camera use case:

- The user frames the page naturally.
- The model sees a crisp still when needed.
- Network/API cost stays tied to intentional questions.
- The camera preview stays local.
- Continuous AI video streaming is deferred.

## Hardware Baseline

- Camera: Logitech C922 at `/dev/video2`
- Mode: MJPG 1920x1080 @ 30fps
- Focus: `focus_absolute=40`
- Sharpness: `180`
- Power line: `power_line_frequency=1` for Tokyo/Japan East 50Hz lighting
- Audio: system default input/output devices, such as AirPods selected in Ubuntu

Apply camera settings before starting the app:

```bash
bash scripts/set_c922_manga_settings.sh /dev/video2
```

## Runtime Flow

1. Start the Realtime snapshot app.

   ```bash
   OPENAI_API_KEY=... python3 scripts/urzasight_realtime_snapshot.py
   ```

2. The app opens a local C922 preview window. Frames are not streamed to the API.

3. The app opens an OpenAI Realtime WebSocket session using `prompts/urzasight_tutor.md` as the tutor instructions.

4. Microphone audio from the system default input is streamed to the Realtime session for speech detection/transcription.

5. When the app detects a trigger phrase such as "Urzasight", "what does this mean", or "explain this", it saves a single JPEG snapshot from the current camera frame.

6. The app sends the snapshot plus the spoken question as a user message.

7. The model answers as Urzasight with short, voice-friendly audio.

8. The answer plays through the system default output device.

## Trigger Semantics

- "Quick" asks for a natural translation only.
- "Break it down" asks for a natural translation plus brief grammar/vocab explanation.
- "Reading" asks for kana readings when possible.
- "Tone" asks for emotional/social tone.
- "Repeat" repeats the last answer without taking a fresh snapshot.
- "What does this mean?", "Urzasight, help", and "Explain this" trigger a fresh snapshot.

## Current Boundary

This prototype intentionally does not send continuous video frames to OpenAI. It sends microphone audio for the voice session and sends a camera image only after a recognized user trigger.
