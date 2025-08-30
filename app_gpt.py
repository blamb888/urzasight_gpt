from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os, io, base64, math, os
from PIL import Image
import pytesseract
import cv2
import numpy as np
from pykakasi import kakasi

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # optional for /explain_gpt

app = FastAPI(title="urzasight_gpt v3")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

def pil_to_cv2(pil_img: Image.Image):
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

def cv2_to_pil(img):
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

def upscale_if_small(img, min_side=900):
    h, w = img.shape[:2]
    s = min(h, w)
    if s >= min_side: return img
    scale = min_side / s
    return cv2.resize(img, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)

def preprocess_for_ocr(cv_img, vertical=True):
    """
    Stronger pipeline for manga:
      - optional rotate for vertical text if crop looks landscape
      - upscale small crops
      - CLAHE contrast
      - light denoise
      - adaptive threshold
      - unsharp for crisp edges
    """
    h, w = cv_img.shape[:2]

    # If vertical text is expected but crop is wider than tall, rotate
    if vertical and w > h:
        cv_img = cv2.rotate(cv_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        h, w = cv_img.shape[:2]

    cv_img = upscale_if_small(cv_img, min_side=1100)

    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)

    # CLAHE to flatten paper texture, pop ink
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)

    # Gentle denoise
    gray = cv2.bilateralFilter(gray, d=7, sigmaColor=50, sigmaSpace=50)

    # Adaptive threshold
    th = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 35, 8)

    # Unsharp mask
    blur = cv2.GaussianBlur(th, (0,0), 1.0)
    sharp = cv2.addWeighted(th, 1.5, blur, -0.5, 0)

    return sharp

def ocr_japanese(pil_img, vertical=False, psm_mode="auto"):
    cv_img = pil_to_cv2(pil_img)
    proc = preprocess_for_ocr(cv_img, vertical=vertical)
    lang = "jpn_vert" if vertical else "jpn"

    # Choose PSM:
    #   6 = block of text (default)
    #   5 = single column (good for vertical bubble)
    #   7 = single line
    psm_map = {"auto": 6, "column": 5, "line": 7}
    psm = psm_map.get(psm_mode, 6)

    config = f"--oem 1 --psm {psm}"
    txt = pytesseract.image_to_string(proc, lang=lang, config=config)
    return txt.strip()

def readings(text):
    kks = kakasi()
    kks.setMode("J", "H")  # Kanji -> Hiragana
    kks.setMode("K", "H")  # Katakana -> Hiragana
    conv = kks.getConverter()
    return {"hiragana": conv.do(text)}

@app.get("/", response_class=HTMLResponse)
def index():
    with open("index_gpt.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/capture_analyze")
async def capture_analyze(
    image_b64: str = Form(...),
    x: int = Form(0), y: int = Form(0),
    w: int = Form(0), h: int = Form(0),
    vertical: int = Form(1),
    psm: str = Form("auto"),           # "auto" | "column" | "line"
):
    header, b64data = image_b64.split(",", 1) if "," in image_b64 else ("", image_b64)
    img_bytes = base64.b64decode(b64data)
    pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")

    if w > 0 and h > 0:
        pil = pil.crop((x, y, x + w, y + h))

    jp = ocr_japanese(pil, vertical=bool(vertical), psm_mode=psm)
    jp = jp.replace("\n", " ").strip()
    pron = readings(jp) if jp else {"hiragana": ""}

    result = {
        "japanese": jp or "",
        "readings": pron,
        "translation": "Tap Explain for a literal → natural translation with grammar.",
    }
    return JSONResponse(result)

@app.post("/explain_gpt")
async def explain_gpt(
    japanese: str = Form(...),
    context_hint: str = Form(""),
):
    jp = (japanese or "").strip()
    if not jp:
        return {"ok": False, "explanation": "No Japanese text provided."}

    # If user has an OpenAI key, call it; otherwise return a local template
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            prompt = f"""
You are a friendly manga reading tutor.
Given this Japanese snippet, produce:
1) Literal translation (word-by-word feel)
2) Natural translation (what it means)
3) Key grammar points (bullet list)
4) Tone/nuance notes (casual? pleading? comedic?)
5) Useful vocab table: kanji | reading | gloss

Japanese: {jp}
Context (optional): {context_hint}
"""
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content":prompt}],
                temperature=0.3,
            )
            text = resp.choices[0].message.content.strip()
            return {"ok": True, "explanation": text}
        except Exception as e:
            return {"ok": False, "explanation": f"LLM call failed: {e}"}

    # Offline fallback
    template = f"""**Literal (rough):**
- (fill-in after checking dictionary) → based on: “{jp}”

**Natural:**
- (paraphrase in clear English)

**Grammar:**
- (1–3 key points: contractions, particles, casual form, negation, etc.)

**Tone/Context:**
- (who’s talking? emotional color?)

**Vocab:**
- Kanji | Reading | Gloss
- — | — | —
"""
    return {"ok": True, "explanation": template}
