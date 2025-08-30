```markdown
# urzasight_gpt 📖🤖

Urzasight GPT is an experimental tool for **live manga reading assistance**.  
It combines a FastAPI backend with a lightweight HTML/JS frontend, enabling OCR + translation workflows directly in the browser.

---

## 🚀 Features
- 📷 **Camera input**: capture manga panels in real-time via phone or webcam
- 🔍 **OCR pipeline**: powered by Tesseract + OpenCV
- 🈶 **Japanese support**: integrates `fugashi`, `unidic-lite`, and `pykakasi` for tokenization + reading
- 🗣️ **Speech feedback**: optional text-to-speech responses (`pyttsx3`)
- 🌐 **HTTPS-ready**: local certs via `mkcert` for browser microphone/camera APIs
- 📱 **Mobile-first UI**: open directly from your phone on LAN (`https://<your-ip>:8443`)

---

## 📂 Project Structure


urzasight\_gpt/
├── app\_gpt.py          # FastAPI backend
├── index\_gpt.html      # Frontend (camera, buttons, OCR/translate hooks)
├── requirements\_gpt.txt# Python dependencies
├── static/             # assets (captures, scripts, etc.)
└── .gitignore          # excludes venv, certs, caches

---

## 🛠️ Installation

### 1. Clone repo
```bash
git clone https://github.com/blamb888/urzasight_gpt.git
cd urzasight_gpt
````

### 2. Setup Python env

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements_gpt.txt
```

### 3. Install system deps

```bash
sudo apt install tesseract-ocr libtesseract-dev
sudo apt install libnss3-tools # needed for mkcert
```

### 4. Local HTTPS cert

```bash
mkcert -install
mkcert 10.42.0.1
```

---

## ▶️ Running

```bash
uvicorn app_gpt:app --host 0.0.0.0 --port 8443 \
  --ssl-keyfile 10.42.0.1-key.pem \
  --ssl-certfile 10.42.0.1.pem
```

Then open on your phone:

```
https://10.42.0.1:8443
```

---

## 📝 TODO / Roadmap

* [ ] Improve OCR accuracy (custom Tesseract model / text orientation fixes)
* [ ] Better speech-to-text for commands
* [ ] UI refinement for region selection
* [ ] GitHub Actions for CI/CD
* [ ] Dockerfile for easy deployment

---

## ⚠️ Disclaimer

This project is experimental and not production-ready. Expect hiccups, especially with OCR accuracy. Contributions welcome!

---

## 📜 License

MIT License © 2025 Brandon Lamb
