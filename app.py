import io
import os
from gtts import gTTS
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

VOICES = [
    {"id": "en-us", "name": "US English",     "accent": "US",    "flag": "🇺🇸"},
    {"id": "en-gb", "name": "UK English",     "accent": "UK",    "flag": "🇬🇧"},
    {"id": "en-au", "name": "Australian",     "accent": "AU",    "flag": "🇦🇺"},
    {"id": "en-ca", "name": "Canadian",       "accent": "Other", "flag": "🇨🇦"},
    {"id": "en-in", "name": "Indian English", "accent": "Other", "flag": "🇮🇳"},
    {"id": "en-ie", "name": "Irish English",  "accent": "Other", "flag": "🇮🇪"},
    {"id": "en-nz", "name": "New Zealand",    "accent": "Other", "flag": "🇳🇿"},
    {"id": "en-za", "name": "South African",  "accent": "Other", "flag": "🇿🇦"},
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
    # Each chunk max 3000 chars — safe limit
    if len(text) > 1500:
        return jsonify({"error": "Chunk too large (max 3000 chars per chunk)"}), 400

    lang = voice if voice.startswith("en-") else "en-us"

    try:
        tts = gTTS(text=text, lang=lang, slow=slow)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return send_file(buf, mimetype="audio/mpeg", as_attachment=False)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
