from rembg import remove
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from PIL import Image
import numpy as np
import base64, json, os, io, time
from urllib.parse import quote
import requests
import time
import replicate
import base64
import io
from dotenv import load_dotenv
load_dotenv()
import traceback
import tempfile
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ─────────────────────────────────────────────
#  SERVE FRONTEND
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/pages/<path:filename>')
def pages(filename):
    return send_from_directory('pages', filename)

# ─────────────────────────────────────────────
#  OUTFIT DATABASE  (rule-based engine)
# ─────────────────────────────────────────────
OUTFITS = {
    "Casual": {
        "Summer":  {"Female": ["floral sundress","crop top with denim shorts","linen co-ord set"],
                    "Male":   ["linen shirt with chino shorts","graphic tee with cargo shorts","polo with slim chinos"]},
        "Winter":  {"Female": ["cozy knit sweater with jeans","oversized hoodie with leggings","turtleneck with corduroy pants"],
                    "Male":   ["chunky knit sweater with dark jeans","fleece jacket with joggers","thermal henley with jeans"]},
        "Spring":  {"Female": ["pastel midi skirt with blouse","denim jacket with floral dress","cardigan with white tee and jeans"],
                    "Male":   ["light jacket with chinos","striped tee with slim pants","bomber jacket with joggers"]},
        "Autumn":  {"Female": ["rust cardigan with skinny jeans","plaid shirt dress with ankle boots","camel coat with turtleneck"],
                    "Male":   ["flannel shirt with dark jeans","utility jacket with chinos","earth-tone hoodie with slim pants"]},
    },
    "Party": {
        "Summer":  {"Female": ["sequin mini dress","wrap dress with heels","off-shoulder bodycon dress"],
                    "Male":   ["slim-fit blazer with turtleneck","linen pastel suit","printed shirt with white trousers"]},
        "Winter":  {"Female": ["velvet bodycon dress","sparkle midi dress with faux fur","black sequin jumpsuit"],
                    "Male":   ["dark suit with silk tie","velvet blazer with black trousers","tuxedo with bow tie"]},
        "Spring":  {"Female": ["floral midi dress","satin slip dress","pastel two-piece set"],
                    "Male":   ["pastel blazer with white shirt","floral print shirt with trousers","light suit with pocket square"]},
        "Autumn":  {"Female": ["deep jewel-toned dress","velvet jumpsuit","metallic skirt with silk blouse"],
                    "Male":   ["burgundy blazer with dark jeans","deep-toned suit","statement jacket with trousers"]},
    },
    "Office": {
        "Summer":  {"Female": ["tailored linen trousers with silk blouse","sheath dress with blazer","midi pencil skirt with fitted top"],
                    "Male":   ["light wool suit","chinos with oxford shirt","slim trousers with polo shirt"]},
        "Winter":  {"Female": ["wool blazer set","tailored trouser suit","knit dress with blazer"],
                    "Male":   ["dark suit with white shirt","wool trousers with sweater","three-piece suit"]},
        "Spring":  {"Female": ["pastel blazer with tailored pants","shirt dress with belt","blouse with A-line skirt"],
                    "Male":   ["navy blazer with grey trousers","chinos with button-down shirt","light suit with tie"]},
        "Autumn":  {"Female": ["camel blazer with tailored trousers","wrap dress with tights","knit top with pencil skirt"],
                    "Male":   ["tweed blazer with dark trousers","herringbone suit","corduroy blazer with chinos"]},
    },
    "Wedding": {
        "Summer":  {"Female": ["flowy chiffon maxi dress","embroidered anarkali","elegant gown with floral details"],
                    "Male":   ["ivory sherwani","light beige suit","printed kurta with churidar"]},
        "Winter":  {"Female": ["velvet lehenga","embellished saree","deep-toned gown"],
                    "Male":   ["dark sherwani with embroidery","three-piece bandhgala suit","royal kurta with jacket"]},
        "Spring":  {"Female": ["pastel lehenga","silk saree with gold border","floral printed gown"],
                    "Male":   ["pastel bandhgala","ivory kurta with churidar","mint green sherwani"]},
        "Autumn":  {"Female": ["rust terracotta lehenga","jewel-toned silk saree","burgundy gown"],
                    "Male":   ["earthy bandhgala","maroon kurta with churidar","gold-detailed sherwani"]},
    },
    "Formal": {
        "Summer":  {"Female": ["white tailored suit","silk blouse with wide-leg trousers","structured shift dress"],
                    "Male":   ["white linen suit","light grey suit with tie","navy blazer with white shirt"]},
        "Winter":  {"Female": ["black power suit","tailored coat dress","structured blazer dress"],
                    "Male":   ["charcoal grey suit","navy three-piece suit","black suit with white pocket square"]},
        "Spring":  {"Female": ["ivory blazer with matching trousers","structured pastel dress","belted coat dress"],
                    "Male":   ["light grey suit with pastel tie","beige suit","blazer with pocket square"]},
        "Autumn":  {"Female": ["camel blazer dress","dark structured suit","tailored coat with trousers"],
                    "Male":   ["dark navy suit","charcoal pinstripe suit","double-breasted blazer with trousers"]},
    },
}

COLOR_MAP = {
    "Neutral":    "beige, white, grey and cream color palette",
    "Bright":     "vibrant red, electric blue and neon yellow color palette",
    "Dark":       "deep black, navy and charcoal color palette",
    "Pastel":     "soft pink, baby blue and lavender color palette",
    "Earthy":     "terracotta, olive green and warm brown color palette",
    "Monochrome": "all-black or all-white monochrome color palette",
    "Vibrant":    "bold multicolor rainbow-inspired color palette",
    "Cool":       "cool blues, teals and purples color palette",
    "Warm":       "warm oranges, reds and yellows color palette",
}

STYLE_ADJECTIVES = {
    "Minimalist": "clean minimal simple silhouette",
    "Luxury":     "luxury designer high-end premium fabric",
    "Streetwear": "urban street style oversized trendy",
    "Officewear": "professional tailored business formal",
    "Romantic":   "feminine floral delicate details",
    "Sporty":     "athletic sporty activewear",
    "Bohemian":   "boho free-spirited flowing fabric",
}

# ─────────────────────────────────────────────
#  API: RECOMMEND
# ─────────────────────────────────────────────
@app.route('/api/recommend', methods=['POST'])
def recommend():
    d = request.json or {}
    body_type = d.get('bodyType', 'Slim')
    gender    = d.get('gender', 'Female')
    occasion  = d.get('occasion', 'Casual')
    season    = d.get('season', 'Summer')
    styles    = d.get('styles', ['Minimalist'])
    color     = d.get('color', 'Neutral')
    budget    = d.get('budget', 'Medium')
    context   = d.get('context', '')

    occ_data    = OUTFITS.get(occasion, OUTFITS['Casual'])
    season_data = occ_data.get(season, list(occ_data.values())[0])
    gen_key     = 'Female' if gender == 'Female' else 'Male'
    options     = season_data.get(gen_key, season_data.get('Female', [
        'elegant outfit', 'stylish ensemble', 'fashionable look']))

    style_desc  = ', '.join([STYLE_ADJECTIVES.get(s, s) for s in styles]) if styles else 'stylish'
    color_desc  = COLOR_MAP.get(color, 'neutral colors')

    results = []
    for i, outfit in enumerate(options[:3]):
        prompt = (
            f"high fashion editorial photography, {outfit}, {style_desc}, "
            f"{color_desc}, {gender.lower()} fashion model, professional studio lighting, "
            f"full body outfit shot, white clean background, Vogue magazine quality, 4k"
        )
        img_url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=512&height=640&nologo=true&seed={i*7+11}"

        results.append({
            "id":          i + 1,
            "name":        outfit.title(),
            "occasion":    occasion,
            "season":      season,
            "style":       ', '.join(styles) if styles else 'Classic',
            "color":       color,
            "budget":      budget,
            "description": (f"A {style_desc} {outfit} perfect for {occasion.lower()} "
                           f"occasions in {season.lower()}. Styled in {color_desc}."),
            "image_url":   img_url,
            "tags":        [occasion, season, gender] + (styles or []),
        })

    return jsonify({"success": True, "outfits": results})


# ─────────────────────────────────────────────
#  API: VIRTUAL TRY-ON  (Fixed + Better Quality)
# ─────────────────────────────────────────────

@app.route('/api/tryon', methods=['POST'])
def tryon():
    try:
        if 'person' not in request.files or 'cloth' not in request.files:
            return jsonify({"success": False, "error": "Upload both person and cloth images"}), 400

        person_file = request.files['person']
        cloth_file = request.files['cloth']

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as p:
            person_file.save(p.name)
            person_path = p.name

        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as c:
            cloth_file.save(c.name)
            cloth_path = c.name

        try:
            output = replicate.run(
                "cuuupid/idm-vton:0513734a452173b8173e907e3a59d19a36266e55b48528559432bd21c7d7e985",
                input={
                    "human_img": open(person_path, "rb"),
                    "garm_img": open(cloth_path, "rb"),
                    
                    "garment_des": "light blue long sleeve knitted button down shirt, soft fabric, professional casual style",
                    "category": "upper_body",
                    "num_samples": 1,
                    "steps": 40,
                    "seed": -1,
                    "guidance_scale": 7.5,
                    
                    # THIS IS THE MOST IMPORTANT FIX
                    "crop": True          # ← Auto-crops if not 3:4
                }
            )

            image_url = output[0] if isinstance(output, list) else str(output)

            return jsonify({
                "success": True,
                "result_image": image_url
            })

        finally:
            for path in [person_path, cloth_path]:
                try:
                    os.unlink(path)
                except:
                    pass

    except Exception as e:
        print(f"🔥 Try-on Error: {type(e).__name__} - {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────
#  API: STYLE ANALYSER
# ─────────────────────────────────────────────
PERSONALITIES = {
    "Minimalist": ("Modern Minimalist",   88, ["Quiet luxury","Clean girl aesthetic","Monochrome sets"]),
    "Luxury":     ("Luxury Fashionista",  93, ["Quiet luxury","Old money aesthetic","Capsule wardrobe"]),
    "Streetwear": ("Urban Trendsetter",   85, ["Y2K revival","Gorpcore","Techwear"]),
    "Bohemian":   ("Free-Spirited Boho",  81, ["Cottagecore","Coastal grandmother","Boho chic"]),
    "Romantic":   ("Romantic Dreamer",    83, ["Balletcore","Coquette aesthetic","Soft girl era"]),
    "Sporty":     ("Active Athlete",      78, ["Athleisure","Gorpcore","Sporty chic"]),
    "Officewear": ("Corporate Chic",      87, ["Corporate casual","Quiet luxury","Power dressing"]),
}

BODY_TIPS = {
    "Slim":     "Structured pieces and layers add beautiful dimension to your frame.",
    "Athletic": "Fitted silhouettes showcase your build perfectly.",
    "Curvy":    "Wrap dresses and A-line silhouettes are your best friends.",
    "Plus":     "Bold prints and vertical lines create stunning elongation.",
    "Petite":   "Monochrome outfits and vertical stripes add lovely height.",
}

COLOR_INSIGHT = {
    "Neutral":    "Your palette is timeless, versatile, and endlessly sophisticated.",
    "Bright":     "You're bold, confident, and unafraid to make a statement.",
    "Dark":       "You lean towards sophisticated, mysterious, powerful tones.",
    "Pastel":     "Soft, romantic, and dreamy — your palette is effortlessly elegant.",
    "Earthy":     "Grounded, natural, and warm — your tones connect with the earth.",
    "Monochrome": "Strong and graphic, your monochrome choices scream editorial.",
    "Vibrant":    "Your vibrant palette radiates energy, joy, and creativity.",
    "Cool":       "Cool, calm, and composed — your palette exudes modern elegance.",
    "Warm":       "Warm and inviting, your palette is full of passion and life.",
}

@app.route('/api/analyse', methods=['POST'])
def analyse():
    try:
        d = request.json or {}
        styles    = d.get('styles', [])
        colors    = d.get('colors', [])
        body_type = d.get('bodyType', 'Slim')
        occasion  = d.get('occasion', 'Casual')
        gender    = d.get('gender', 'Female')

        top_style = styles[0] if styles else 'Minimalist'
        personality, score, trends = PERSONALITIES.get(top_style, ("Classic Elegance", 75, ["Timeless fashion"]))

        # Boost score for more styles selected
        score = min(98, score + len(styles) * 2)

        tips = []
        tips.append(BODY_TIPS.get(body_type, "Experiment freely with different cuts and fits."))
        if len(styles) > 1:
            tips.append(f"Your mix of {' + '.join(styles)} creates a uniquely personal aesthetic.")

        palette_note = COLOR_INSIGHT.get(colors[0] if colors else 'Neutral',
                                         "Your color palette is beautifully balanced.")

        return jsonify({
            "success":             True,
            "personality":         personality,
            "score":               score,
            "tips":                tips,
            "palette_insight":     palette_note,
            "trending_aesthetics": trends,
            "style_summary":       (
                f"You are a {personality} who gravitates towards "
                f"{', '.join(styles) if styles else 'classic'} fashion "
                f"in {colors[0] if colors else 'neutral'} tones — "
                f"a perfect match for {occasion.lower()} occasions."
            ),
            "wardrobe_essentials": _wardrobe_essentials(top_style, gender),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def _wardrobe_essentials(style, gender):
    essentials = {
        "Minimalist": ["White button-down shirt","Black slim trousers","Beige trench coat","White sneakers","Black belt"],
        "Luxury":     ["Cashmere sweater","Tailored blazer","Silk blouse","Leather loafers","Statement watch"],
        "Streetwear": ["Oversized hoodie","Cargo pants","Chunky sneakers","Graphic tee","Bucket hat"],
        "Bohemian":   ["Flowy maxi skirt","Embroidered blouse","Leather sandals","Fringe bag","Layered necklaces"],
        "Romantic":   ["Floral midi dress","Lace-trim blouse","Mary Jane heels","Pearl earrings","Pastel cardigan"],
        "Sporty":     ["Athletic leggings","Performance jacket","Running shoes","Sports bra","Zip-up hoodie"],
        "Officewear": ["Tailored blazer","Pencil skirt","Oxford shirt","Block-heel pumps","Structured handbag"],
    }
    return essentials.get(style, ["White shirt","Dark jeans","Blazer","Clean sneakers","Classic watch"])


# ─────────────────────────────────────────────
#  API: WARDROBE  (JSON file storage)
# ─────────────────────────────────────────────
WARDROBE_FILE = 'wardrobe_data.json'

def load_wardrobe():
    if os.path.exists(WARDROBE_FILE):
        with open(WARDROBE_FILE) as f:
            return json.load(f)
    return []

def save_wardrobe(items):
    with open(WARDROBE_FILE, 'w') as f:
        json.dump(items, f, indent=2)

@app.route('/api/wardrobe', methods=['GET'])
def get_wardrobe():
    return jsonify({"success": True, "items": load_wardrobe()})

@app.route('/api/wardrobe', methods=['POST'])
def add_item():
    try:
        d = request.json or {}
        items = load_wardrobe()
        item = {
            "id":         int(time.time() * 1000),
            "name":       d.get('name', 'My Outfit'),
            "category":   d.get('category', 'Top'),
            "color":      d.get('color', 'Neutral'),
            "occasion":   d.get('occasion', 'Casual'),
            "season":     d.get('season', 'All Season'),
            "image_url":  d.get('image_url', ''),
            "notes":      d.get('notes', ''),
            "added_date": time.strftime('%Y-%m-%d'),
        }
        items.append(item)
        save_wardrobe(items)
        return jsonify({"success": True, "item": item})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/wardrobe/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    try:
        items = [i for i in load_wardrobe() if i['id'] != item_id]
        save_wardrobe(items)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ─────────────────────────────────────────────
#  API: GENERATE IMAGE  (Pollinations proxy)
# ─────────────────────────────────────────────
@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    prompt = (request.json or {}).get('prompt', 'fashion outfit')
    url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?width=512&height=640&nologo=true"
    return jsonify({"success": True, "image_url": url})


# ====================== GEMINI INTEGRATION (New) ======================
# Added for your frontend call to /api/recommend-gemini
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    if GEMINI_API_KEY:
        gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        print("✅ Gemini client ready (using google-genai)")
    else:
        gemini_client = None
        print("⚠️ GEMINI_API_KEY not found in .env")
except ImportError:
    gemini_client = None
    print("⚠️ Run: pip install google-genai")

@app.route('/api/recommend-gemini', methods=['POST'])
def recommend_gemini():
    try:
        if not gemini_client:
            return jsonify({"success": False, "error": "Gemini not configured. Check API key."}), 500

        d = request.get_json(force=True) or {}
        gender = d.get('gender', 'Female')
        body_type = d.get('bodyType', 'Slim')
        occasion = d.get('occasion', 'Casual')
        season = d.get('season', 'Summer')
        styles = d.get('styles', ['Minimalist'])
        budget = d.get('budget', '')
        context = d.get('context', '')

        prompt = f"""You are a professional fashion stylist for VOGUE.AI.
User Profile:
- Gender: {gender}
- Body Type: {body_type}
- Occasion: {occasion}
- Season: {season}
- Preferred Styles: {', '.join(styles)}
- Budget: {budget}
- Additional Context: {context}

Provide a beautiful, detailed outfit recommendation with specific clothing items, colors, accessories and styling tips. Make it exciting like a Vogue article."""

        # Try lighter model first to avoid 503
        try:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash-lite",   # lighter & more available
                contents=[prompt]
            )
        except Exception:
            # Fallback to original if lite fails
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )

        return jsonify({"success": True, "response": response.text})

    except Exception as e:
        print(f"Gemini Error: {e}")
        traceback.print_exc()
        error_str = str(e).lower()
        if "503" in error_str or "high demand" in error_str or "unavailable" in error_str:
            return jsonify({"success": False, "error": "Gemini is currently overloaded (high demand). Please wait 5-10 minutes and try again."}), 503
        return jsonify({"success": False, "error": "AI service error. Please try again later."}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, port=port, host='0.0.0.0')
