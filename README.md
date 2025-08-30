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
