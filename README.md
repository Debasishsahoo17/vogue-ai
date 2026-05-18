# VOGUE.AI — AI Fashion System

## Quick Start (2 steps)

### 1. Install dependencies
```bash
pip install flask flask-cors pillow numpy
```

### 2. Run the backend
```bash
python app.py
```

Then open your browser and go to:
```
http://localhost:5000
```

---

## Project Structure

```
vogue-ai/
├── app.py              ← Flask backend (run this)
├── requirements.txt
├── index.html          ← Homepage
├── style.css
├── script.js
└── pages/
    ├── recommend.html  ← AI Outfit Generator (Pollinations.ai images)
    ├── tryon.html      ← Virtual Try-On (PIL overlay demo)
    ├── analyse.html    ← Style Analyser (rule-based AI)
    ├── wardrobe.html   ← Wardrobe Manager (JSON storage)
    ├── about.html
    ├── contact.html
    └── signup.html
```

---

## Features & APIs

| Page | Endpoint | What it does |
|---|---|---|
| Recommend | `POST /api/recommend` | Rule-based outfit engine → Pollinations.ai images |
| Try-On | `POST /api/tryon` | PIL image overlay demo |
| Analyse | `POST /api/analyse` | Style personality + score + tips |
| Wardrobe | `GET/POST/DELETE /api/wardrobe` | JSON file storage |

---

## Image Generation (FREE — no API key)

Uses **Pollinations.ai** — completely free, no signup needed.

Example URL:
```
https://image.pollinations.ai/prompt/elegant%20red%20dress%20fashion%20photo
```

---

## Notes

- Backend runs on `http://localhost:5000`
- Wardrobe data saved to `wardrobe_data.json` in project root
- No GPU needed — all processing runs on CPU
- Works fully offline except for Pollinations.ai image generation
