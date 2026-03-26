import io
import os
from gtts import gTTS
from pydub import AudioSegment
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

CHUNK_SIZE = 3000  # chars per chunk — safe for gTTS

def split_text(text, size=CHUNK_SIZE):
    """Split text into chunks at sentence boundaries."""
    chunks = []
    while len(text) > size:
        # Try to split at sentence end
        split_at = size
        for sep in ['. ', '! ', '? ', '\n', ', ', ' ']:
            idx = text.rfind(sep, 0, size)
            if idx > size // 2:
                split_at = idx + len(sep)
                break
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks

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
    chunks = split_text(text)

    try:
        if len(chunks) == 1:
            # Single chunk — direct
            tts = gTTS(text=chunks[0], lang=lang, slow=slow)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
        else:
            # Multiple chunks — merge with pydub
            combined = AudioSegment.empty()
            for chunk in chunks:
                tts = gTTS(text=chunk, lang=lang, slow=slow)
                chunk_buf = io.BytesIO()
                tts.write_to_fp(chunk_buf)
                chunk_buf.seek(0)
                seg = AudioSegment.from_mp3(chunk_buf)
                combined += seg
            buf = io.BytesIO()
            combined.export(buf, format="mp3")
            buf.seek(0)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    voice_obj = next((v for v in VOICES if v["id"] == voice), VOICES[0])
    filename  = f"voicecraft-{voice_obj['name'].split()[0].lower()}-{os.urandom(4).hex()}.mp3"

    return send_file(buf, mimetype="audio/mpeg", as_attachment=True, download_name=filename)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
