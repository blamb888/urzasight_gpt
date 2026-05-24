# Codex / AI Agent Instructions — urzasight_gpt

Quick orientation (what this repo is):
- Small FastAPI-based web tool for extracting Japanese text from images and providing explanations.
- Core server: `app_gpt.py` (serves UI, OCR endpoints, and an optional LLM-backed explainer).
- Client UI: `index_gpt.html` (camera preview, ROI selection, form POSTs to server endpoints).
- Dependencies: listed in `requirements_gpt.txt` (includes Tesseract/OCR helpers and Japanese tooling).

Architecture & key flows
- The single FastAPI app mounts static files from the `static/` directory and serves `index_gpt.html` at `/`.
- OCR flow: the client captures or uploads an image (data URL) and POSTs to `/capture_analyze` with optional ROI (`x,y,w,h`) and flags (`vertical`, `psm`). See `index_gpt.html` JS for exact form fields.
- Explanation flow: after OCR, the UI posts `japanese` to `/explain_gpt`. If `OPENAI_API_KEY` is set, the server will call OpenAI; otherwise it returns a local template.

Project-specific conventions & patterns
- File suffix: many project files use `_gpt` in the name (e.g., `app_gpt.py`, `index_gpt.html`, `requirements_gpt.txt`). Keep that convention for any parallel examples or demo files.
- OCR pipeline lives in `app_gpt.py`: functions `preprocess_for_ocr`, `ocr_japanese`, and `readings` (uses `pykakasi`). Important behaviors:
  - `preprocess_for_ocr` upscales small crops, applies CLAHE, denoise, adaptive threshold, and an unsharp mask — tuned for manga/comic bubbles.
  - `ocr_japanese` selects `jpn` vs `jpn_vert` and maps `psm` modes: `auto` → 6, `column` → 5, `line` → 7.
  - ROI handling: the client computes pixel-scaled ROI and sends `x,y,w,h` to server; server crops the PIL image when `w,h > 0`.
- UI-driven assumptions: the front-end favors high-resolution camera frames and expects HTTPS for camera access. The app exposes permissive CORS for quick local testing.

Dependencies & system requirements
- Python reqs: see `requirements_gpt.txt`. Install with `pip install -r requirements_gpt.txt`.
- System-level: Tesseract OCR binary must be installed and available to `pytesseract`. For Japanese OCR you may need appropriate tesseract language packs (e.g., `jpn` and `jpn_vert`) and `unidic-lite` for morphological analysis.
- Optional: set `OPENAI_API_KEY` in the environment to enable `/explain_gpt` LLM calls.

Developer workflows (common tasks)
- Run dev server locally:
  - `uvicorn app_gpt:app --reload --host 0.0.0.0 --port 8000`
- Test OCR flow manually: open `/` in a browser (served by the app) and use the camera UI or upload a hi-res still, draw an ROI, then tap “Ask urzasight_gpt”.
- Call explanation endpoint directly (example):
  - `curl -X POST -F "japanese=今日は" http://localhost:8000/explain_gpt`

Guidance for AI agents (what to do first)
- Read `app_gpt.py` start-to-finish to understand the image pipeline and the two HTTP endpoints: `/capture_analyze` and `/explain_gpt`.
- Inspect `index_gpt.html` for the exact client-side field names and UI expectations (data URL format, ROI math, `vertical` and `psm` values). Copy exact keys when forming requests.
- If modifying OCR parameters, test with real images using the UI — the preprocessing is tuned for manga-style input and small changes have visible effects.
- When adding dependencies: update `requirements_gpt.txt`; avoid changing the `_gpt` naming unless intentionally refactoring conventions.

Examples and snippets (use these to validate changes)
- Sample POST to analyze (ROI optional):
  - Form fields: `image_b64` (data URL), `x`, `y`, `w`, `h`, `vertical` (0/1), `psm` (`auto|column|line`).
- Sample explain call:
  - `curl -X POST -F "japanese=彼は行った" http://localhost:8000/explain_gpt`

What not to assume
- There are no tests in the repo — changes affecting OCR quality require manual verification with sample images.
- The project assumes system-level OCR support (Tesseract). Installing Python packages is not sufficient alone.

Where to look for edits
- Server logic and OCR tuning: `app_gpt.py`.
- UI behavior and field names: `index_gpt.html`.
- Python deps snapshot: `requirements_gpt.txt`.

If anything here is unclear or you want me to expand examples (cURL with base64 payload, Dockerfile, or automated tests), tell me which part and I will update the file.
