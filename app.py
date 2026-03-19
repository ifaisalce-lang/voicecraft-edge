import io
import os
from gtts import gTTS
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

VOICES = [
    {"id": "en-us", "name": "Aria (US)",     "gender": "Female", "accent": "US", "style": "Natural"},
    {"id": "en-gb", "name": "Sonia (UK)",    "gender": "Female", "accent": "UK", "style": "British"},
    {"id": "en-au", "name": "Natasha (AU)",  "gender": "Female", "accent": "AU", "style": "Australian"},
    {"id": "en-ca", "name": "Clara (CA)",    "gender": "Female", "accent": "CA", "style": "Canadian"},
    {"id": "en-in", "name": "Neerja (IN)",   "gender": "Female", "accent": "IN", "style": "Indian"},
    {"id": "en-ie", "name": "Emily (IE)",    "gender": "Female", "accent": "IE", "style": "Irish"},
    {"id": "en-nz", "name": "Molly (NZ)",    "gender": "Female", "accent": "NZ", "style": "New Zealand"},
    {"id": "en-za", "name": "Ayanda (ZA)",   "gender": "Female", "accent": "ZA", "style": "South African"},
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/voices")
def get_voices():
    return jsonify(VOICES)

@app.route("/synthesize", methods=["POST"])
def synthesize():
    data  = request.get_json()
    text  = (data.get("text") or "").strip()
    voice = data.get("voice", "en-us")
    slow  = data.get("slow", False)

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if len(text) > 50000:
        return jsonify({"error": "Text too long (max 50,000 chars)"}), 400

    lang = voice if voice.startswith("en-") else "en-us"

    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    voice_name = next((v["name"] for v in VOICES if v["id"] == voice), "voice")
    filename   = f"voicecraft-{voice_name.split()[0].lower()}-{os.urandom(4).hex()}.mp3"

    return send_file(buf, mimetype="audio/mpeg", as_attachment=True, download_name=filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
