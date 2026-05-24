#!/usr/bin/env python3
"""Urzasight Realtime voice + C922 snapshot MVP."""

from __future__ import annotations

import argparse
import base64
import json
import os
import queue
import signal
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT = ROOT / "prompts" / "urzasight_tutor.md"
DEFAULT_OUTPUT_DIR = ROOT / "captures"

TRIGGER_PHRASES = (
    "urzasight",
    "what does this mean",
    "what's this mean",
    "what does that mean",
    "what exactly does that mean",
    "what is this kanji",
    "what's this kanji",
    "this kanji",
    "these two kanji",
    "explain this",
    "explain that",
    "help me read this",
    "can you read this",
    "could you read this",
    "how do i read this",
    "could it mean",
    "how was that",
    "reading",
    "tone",
    "break it down",
    "quick",
    "help me",
    "help",
)
WAKE_PHRASES = ("urzasight",)
REPEAT_PHRASES = ("repeat", "say that again", "again")
VISUAL_FOLLOWUP_HINTS = (
    "this",
    "that",
    "kanji",
    "mean",
    "read",
    "passage",
    "bubble",
    "panel",
    "word",
)
JAPANESE_CHAR_RANGES = (
    ("\u3040", "\u309f"),
    ("\u30a0", "\u30ff"),
    ("\u3400", "\u4dbf"),
    ("\u4e00", "\u9fff"),
)


@dataclass
class CameraState:
    latest_frame: Any | None = None
    latest_path: Path | None = None


@dataclass
class TutorSessionState:
    active: bool = False
    response_active: bool = False
    active_response_id: str | None = None
    recent_reading: str = ""


@dataclass
class PendingResponse:
    kind: str
    transcript: str = ""
    image_path: Path | None = None
    recent_reading: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Urzasight Realtime voice + snapshot MVP."
    )
    parser.add_argument("--device", default="/dev/video2", help="C922 device path.")
    parser.add_argument("--width", type=int, default=1920, help="Capture width.")
    parser.add_argument("--height", type=int, default=1080, help="Capture height.")
    parser.add_argument("--format", default="MJPG", help="Camera fourcc format.")
    parser.add_argument("--fps", type=float, default=30, help="Camera FPS.")
    parser.add_argument("--model", default="gpt-realtime", help="Realtime model.")
    parser.add_argument("--voice", default="alloy", help="Realtime output voice.")
    parser.add_argument("--prompt", default=str(DEFAULT_PROMPT), help="Tutor prompt path.")
    parser.add_argument(
        "--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Snapshot directory."
    )
    parser.add_argument(
        "--audio-rate", type=int, default=24000, help="PCM16 mono audio sample rate."
    )
    parser.add_argument(
        "--audio-block-ms", type=int, default=100, help="Microphone chunk size."
    )
    parser.add_argument(
        "--no-preview", action="store_true", help="Run without a local camera window."
    )
    return parser.parse_args()


def device_index(device: str) -> int | str:
    prefix = "/dev/video"
    if device.startswith(prefix):
        suffix = device.removeprefix(prefix)
        if suffix.isdigit():
            return int(suffix)
    return device


def load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def import_dependencies() -> tuple[Any, Any, Any]:
    missing: list[str] = []
    try:
        import cv2
    except ImportError:
        cv2 = None
        missing.append("opencv-python")
    try:
        import sounddevice as sd
    except ImportError:
        sd = None
        missing.append("sounddevice")
    try:
        import websocket
    except ImportError:
        websocket = None
        missing.append("websocket-client")

    if missing:
        packages = " ".join(missing)
        raise SystemExit(
            "Missing Python package(s): "
            f"{', '.join(missing)}\n"
            f"Install with: python3 -m pip install {packages}"
        )

    return cv2, sd, websocket


def make_data_url(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def snapshot_filename() -> str:
    return f"manga_snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"


def contains_japanese(text: str) -> bool:
    return any(start <= char <= end for char in text for start, end in JAPANESE_CHAR_RANGES)


def looks_like_visual_followup(transcript: str) -> bool:
    lowered = transcript.lower()
    if "?" in lowered:
        return True
    return any(hint in lowered for hint in VISUAL_FOLLOWUP_HINTS)


def detect_command(transcript: str, session_active: bool) -> str | None:
    lowered = transcript.lower()
    if any(phrase in lowered for phrase in REPEAT_PHRASES):
        return "repeat"
    if lowered.strip(" .,!?:;") in WAKE_PHRASES:
        return "wake"
    if "how was that" in lowered:
        return "reading_feedback"
    if any(phrase in lowered for phrase in TRIGGER_PHRASES):
        return "snapshot"
    if session_active and looks_like_visual_followup(transcript):
        return "snapshot"
    return None


def style_hint(transcript: str) -> str:
    lowered = transcript.lower()
    if "how was that" in lowered:
        return (
            "Reading feedback mode: evaluate the user's recent reading gently. "
            "Use the image as the source of truth."
        )
    if "quick" in lowered:
        return "Quick mode: give the natural English meaning only."
    if "break it down" in lowered:
        return "Breakdown mode: give the meaning, then brief grammar and vocabulary."
    if "reading" in lowered:
        return "Reading mode: include Japanese readings in kana when possible."
    if "tone" in lowered:
        return "Tone mode: focus on emotional and social tone."
    return "Default mode: short natural meaning, then a brief Japanese breakdown."


def send_event(ws: Any, payload: dict[str, Any]) -> None:
    ws.send(json.dumps(payload, ensure_ascii=False))


def send_snapshot_question(
    ws: Any,
    image_path: Path,
    transcript: str,
    instructions: str,
    recent_reading: str = "",
) -> None:
    question = transcript.strip() or "Urzasight, help me understand this manga panel."
    reading_context = ""
    if recent_reading:
        reading_context = (
            "\nRecent possible reading practice transcript from the user: "
            f"{recent_reading}\n"
            "Do not over-trust this transcript if it sounds like broken Japanese. "
            "Use the image as the source of truth."
        )
    send_event(
        ws,
        {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": (
                            f"Spoken user question: {question}\n"
                            f"{style_hint(question)}\n"
                            f"{reading_context}"
                            "Answer aloud as Urzasight."
                        ),
                    },
                    {
                        "type": "input_image",
                        "image_url": make_data_url(image_path),
                        "detail": "high",
                    },
                ],
            },
        },
    )
    send_event(
        ws,
        {
            "type": "response.create",
            "response": {
                "instructions": instructions,
                "output_modalities": ["audio"],
            },
        },
    )


def send_repeat(ws: Any) -> None:
    send_event(
        ws,
        {
            "type": "response.create",
            "response": {
                "instructions": "Repeat your last answer briefly and clearly.",
                "output_modalities": ["audio"],
            },
        },
    )


def clear_audio_queue(audio_queue: "queue.Queue[bytes]") -> None:
    while True:
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break


def cancel_active_response(
    ws: Any, tutor_state: TutorSessionState, audio_queue: "queue.Queue[bytes]"
) -> None:
    if not tutor_state.response_active:
        return
    clear_audio_queue(audio_queue)
    payload: dict[str, Any] = {"type": "response.cancel"}
    if tutor_state.active_response_id:
        payload["response_id"] = tutor_state.active_response_id
    send_event(ws, payload)


def camera_loop(
    cv2: Any,
    state: CameraState,
    lock: threading.Lock,
    stop: threading.Event,
    args: argparse.Namespace,
) -> None:
    cap = cv2.VideoCapture(device_index(args.device), cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"Could not open camera device: {args.device}", file=sys.stderr)
        stop.set()
        return

    fourcc = cv2.VideoWriter_fourcc(*args.format[:4].upper())
    cap.set(cv2.CAP_PROP_FOURCC, fourcc)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)
    cap.set(cv2.CAP_PROP_FPS, args.fps)

    try:
        while not stop.is_set():
            ok, frame = cap.read()
            if not ok or frame is None:
                print(f"Could not read a frame from: {args.device}", file=sys.stderr)
                stop.set()
                break

            with lock:
                state.latest_frame = frame.copy()

            if not args.no_preview:
                display = frame.copy()
                cv2.putText(
                    display,
                    "Urzasight local preview: say 'explain this' to capture",
                    (24, 42),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )
                cv2.imshow("Urzasight local C922 preview", display)
                key = cv2.waitKey(1) & 0xFF
                if key in (27, ord("q"), ord("Q")):
                    stop.set()
                    break
            else:
                time.sleep(0.001)
    finally:
        cap.release()
        if not args.no_preview:
            cv2.destroyAllWindows()


def save_current_snapshot(
    cv2: Any,
    state: CameraState,
    lock: threading.Lock,
    output_dir: Path,
) -> Path | None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with lock:
        frame = None if state.latest_frame is None else state.latest_frame.copy()

    if frame is None:
        print("No camera frame available yet; try again in a moment.")
        return None

    path = output_dir / snapshot_filename()
    if not cv2.imwrite(str(path), frame):
        print(f"Could not write snapshot: {path}")
        return None

    with lock:
        state.latest_path = path
    print(f"Snapshot: {path}")
    return path


def audio_input_loop(
    sd: Any,
    ws: Any,
    app_stop: threading.Event,
    session_stop: threading.Event,
    rate: int,
    block_ms: int,
) -> None:
    blocksize = max(1, int(rate * block_ms / 1000))

    def callback(indata: bytes, frames: int, time_info: Any, status: Any) -> None:
        if app_stop.is_set() or session_stop.is_set():
            raise sd.CallbackStop
        if status:
            print(f"Audio input status: {status}", file=sys.stderr)
        audio_b64 = base64.b64encode(indata).decode("ascii")
        try:
            send_event(ws, {"type": "input_audio_buffer.append", "audio": audio_b64})
        except Exception as exc:  # noqa: BLE001
            print(f"Audio send failed: {exc}", file=sys.stderr)
            session_stop.set()

    with sd.RawInputStream(
        samplerate=rate,
        channels=1,
        dtype="int16",
        blocksize=blocksize,
        callback=callback,
    ):
        while not app_stop.is_set() and not session_stop.is_set():
            time.sleep(0.1)


def audio_output_loop(
    sd: Any, stop: threading.Event, audio_queue: "queue.Queue[bytes]", rate: int
) -> None:
    pending = bytearray()

    def callback(outdata: bytearray, frames: int, time_info: Any, status: Any) -> None:
        nonlocal pending
        if status:
            print(f"Audio output status: {status}", file=sys.stderr)
        needed = frames * 2
        while len(pending) < needed:
            try:
                pending.extend(audio_queue.get_nowait())
            except queue.Empty:
                break
        chunk = bytes(pending[:needed])
        del pending[:needed]
        if len(chunk) < needed:
            chunk += b"\x00" * (needed - len(chunk))
        outdata[:] = chunk

    with sd.RawOutputStream(samplerate=rate, channels=1, dtype="int16", callback=callback):
        while not stop.is_set():
            time.sleep(0.1)


def configure_session(ws: Any, prompt: str, voice: str, rate: int) -> None:
    send_event(
        ws,
        {
            "type": "session.update",
            "session": {
                "type": "realtime",
                "instructions": prompt,
                "output_modalities": ["audio"],
                "audio": {
                    "input": {
                        "format": {"type": "audio/pcm", "rate": rate},
                        "transcription": {
                            "model": "gpt-4o-transcribe",
                            "language": "en",
                            "prompt": (
                                "The user is asking spoken manga-reading questions. "
                                "Transcribe trigger phrases like Urzasight, explain this, "
                                "what does this mean, quick, break it down, reading, tone, repeat."
                            ),
                        },
                        "turn_detection": {
                            "type": "server_vad",
                            "create_response": False,
                            "interrupt_response": True,
                            "silence_duration_ms": 700,
                        },
                    },
                    "output": {
                        "format": {"type": "audio/pcm", "rate": rate},
                        "voice": voice,
                    },
                },
            },
        },
    )


def realtime_event_loop(
    websocket: Any,
    cv2: Any,
    ws: Any,
    args: argparse.Namespace,
    prompt: str,
    camera_state: CameraState,
    camera_lock: threading.Lock,
    app_stop: threading.Event,
    session_stop: threading.Event,
    audio_queue: "queue.Queue[bytes]",
) -> None:
    tutor_state = TutorSessionState()
    pending_response: PendingResponse | None = None

    def start_response(request: PendingResponse) -> None:
        if request.kind == "repeat":
            send_repeat(ws)
        elif request.kind == "snapshot" and request.image_path is not None:
            send_snapshot_question(
                ws,
                request.image_path,
                request.transcript,
                prompt,
                request.recent_reading,
            )
        tutor_state.response_active = True
        tutor_state.active_response_id = None

    def start_or_queue_response(request: PendingResponse) -> None:
        nonlocal pending_response
        if tutor_state.response_active:
            pending_response = request
            cancel_active_response(ws, tutor_state, audio_queue)
            return
        start_response(request)

    while not app_stop.is_set() and not session_stop.is_set():
        try:
            raw = ws.recv()
        except websocket.WebSocketTimeoutException:
            continue
        except websocket.WebSocketConnectionClosedException:
            print("Realtime connection closed.")
            session_stop.set()
            break
        except Exception as exc:  # noqa: BLE001
            print(f"Realtime receive failed: {exc}", file=sys.stderr)
            session_stop.set()
            break

        if not raw:
            continue

        event = json.loads(raw)
        event_type = event.get("type")

        if event_type == "error":
            error = event.get("error") or {}
            print(f"Realtime error: {error}", file=sys.stderr)
            if error.get("code") == "conversation_already_has_active_response":
                cancel_active_response(ws, tutor_state, audio_queue)
                continue
            print("Realtime is unavailable; keeping the local camera preview open.")
            session_stop.set()
            break
        if event_type == "response.created":
            response = event.get("response") or {}
            tutor_state.response_active = True
            tutor_state.active_response_id = response.get("id")
        elif event_type == "response.done":
            tutor_state.response_active = False
            tutor_state.active_response_id = None
            if pending_response is not None:
                request = pending_response
                pending_response = None
                start_response(request)
        elif event_type == "conversation.item.input_audio_transcription.completed":
            transcript = event.get("transcript", "").strip()
            if not transcript:
                continue
            print(f"Heard: {transcript}")
            if any(phrase in transcript.lower() for phrase in WAKE_PHRASES):
                tutor_state.active = True
            command = detect_command(transcript, tutor_state.active)
            if command == "wake":
                print("Urzasight session is active.")
            elif command == "repeat":
                start_or_queue_response(PendingResponse(kind="repeat"))
            elif command == "reading_feedback":
                tutor_state.active = True
                path = save_current_snapshot(
                    cv2, camera_state, camera_lock, Path(args.output_dir)
                )
                if path:
                    start_or_queue_response(
                        PendingResponse(
                            kind="snapshot",
                            transcript=transcript,
                            image_path=path,
                            recent_reading=tutor_state.recent_reading,
                        )
                    )
            elif command == "snapshot":
                tutor_state.active = True
                path = save_current_snapshot(
                    cv2, camera_state, camera_lock, Path(args.output_dir)
                )
                if path:
                    recent_reading = (
                        tutor_state.recent_reading if contains_japanese(transcript) else ""
                    )
                    start_or_queue_response(
                        PendingResponse(
                            kind="snapshot",
                            transcript=transcript,
                            image_path=path,
                            recent_reading=recent_reading,
                        )
                    )
            else:
                if contains_japanese(transcript):
                    tutor_state.recent_reading = transcript
                    print("Stored possible reading practice transcript.")
                else:
                    print("No snapshot trigger detected.")
        elif event_type == "response.output_audio.delta":
            delta = event.get("delta")
            if delta:
                audio_queue.put(base64.b64decode(delta))
        elif event_type == "response.output_audio_transcript.delta":
            delta = event.get("delta")
            if delta:
                print(delta, end="", flush=True)
        elif event_type == "response.output_audio_transcript.done":
            print()


def realtime_session_loop(
    websocket: Any,
    cv2: Any,
    sd: Any,
    args: argparse.Namespace,
    prompt: str,
    camera_state: CameraState,
    camera_lock: threading.Lock,
    app_stop: threading.Event,
    audio_queue: "queue.Queue[bytes]",
) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("OPENAI_API_KEY is not set. Local camera preview only.", file=sys.stderr)
        return

    session_stop = threading.Event()
    input_thread: threading.Thread | None = None
    ws = None

    try:
        url = f"wss://api.openai.com/v1/realtime?model={args.model}"
        ws = websocket.create_connection(
            url,
            header=[f"Authorization: Bearer {api_key}"],
            timeout=10,
        )
        ws.settimeout(1)
        configure_session(ws, prompt, args.voice, args.audio_rate)

        input_thread = threading.Thread(
            target=audio_input_loop,
            args=(
                sd,
                ws,
                app_stop,
                session_stop,
                args.audio_rate,
                args.audio_block_ms,
            ),
            daemon=True,
        )
        input_thread.start()

        print("Urzasight Realtime connected.")
        print("Say: 'Urzasight', 'what does this mean', or 'explain this'.")
        print("Say: 'repeat' to repeat the last answer. Press Q in preview or Ctrl+C to quit.")

        realtime_event_loop(
            websocket,
            cv2,
            ws,
            args,
            prompt,
            camera_state,
            camera_lock,
            app_stop,
            session_stop,
            audio_queue,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Realtime startup failed: {exc}", file=sys.stderr)
        print("Local camera preview is still available.")
    finally:
        session_stop.set()
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass
        if input_thread:
            input_thread.join(timeout=2)


def main() -> int:
    args = parse_args()
    cv2, sd, websocket = import_dependencies()
    prompt = load_prompt(Path(args.prompt))
    stop = threading.Event()
    camera_state = CameraState()
    camera_lock = threading.Lock()
    audio_queue: "queue.Queue[bytes]" = queue.Queue()

    def request_stop(signum: int, frame: Any) -> None:
        stop.set()

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)

    output_thread = threading.Thread(
        target=audio_output_loop,
        args=(sd, stop, audio_queue, args.audio_rate),
        daemon=True,
    )
    output_thread.start()

    realtime_thread: threading.Thread | None = None

    try:
        realtime_thread = threading.Thread(
            target=realtime_session_loop,
            args=(
                websocket,
                cv2,
                sd,
                args,
                prompt,
                camera_state,
                camera_lock,
                stop,
                audio_queue,
            ),
            daemon=True,
        )
        realtime_thread.start()

        print("Opening local C922 preview. Frames are not streamed to the API.")
        print("Press Q or Esc in the preview window to quit.")
        camera_loop(cv2, camera_state, camera_lock, stop, args)
    finally:
        stop.set()
        if realtime_thread:
            realtime_thread.join(timeout=2)
        output_thread.join(timeout=2)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
