import asyncio
import io
import os
import edge_tts
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# All good English voices from Edge TTS
VOICES = [
    {"id": "en-US-AriaNeural",      "name": "Aria",      "gender": "Female", "style": "Natural, warm"},
    {"id": "en-US-JennyNeural",     "name": "Jenny",     "gender": "Female", "style": "Friendly, clear"},
    {"id": "en-US-SaraNeural",      "name": "Sara",      "gender": "Female", "style": "Cheerful"},
    {"id": "en-US-NancyNeural",     "name": "Nancy",     "gender": "Female", "style": "Pleasant"},
    {"id": "en-US-MichelleNeural",  "name": "Michelle",  "gender": "Female", "style": "Friendly"},
    {"id": "en-US-MonicaNeural",    "name": "Monica",    "gender": "Female", "style": "Warm"},
    {"id": "en-US-GuyNeural",       "name": "Guy",       "gender": "Male",   "style": "Natural, deep"},
    {"id": "en-US-ChristopherNeural","name": "Christopher","gender": "Male", "style": "Reliable"},
    {"id": "en-US-EricNeural",      "name": "Eric",      "gender": "Male",   "style": "Rational"},
    {"id": "en-US-RogerNeural",     "name": "Roger",     "gender": "Male",   "style": "Lively"},
    {"id": "en-US-SteffanNeural",   "name": "Steffan",   "gender": "Male",   "style": "Calm"},
    {"id": "en-GB-SoniaNeural",     "name": "Sonia (UK)", "gender": "Female","style": "British accent"},
    {"id": "en-GB-RyanNeural",      "name": "Ryan (UK)", "gender": "Male",   "style": "British accent"},
    {"id": "en-AU-NatashaNeural",   "name": "Natasha (AU)","gender": "Female","style": "Australian"},
    {"id": "en-AU-WilliamNeural",   "name": "William (AU)","gender": "Male", "style": "Australian"},
]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/voices")
def get_voices():
    return jsonify(VOICES)

@app.route("/synthesize", methods=["POST"])
def synthesize():
    data    = request.get_json()
    text    = (data.get("text") or "").strip()
    voice   = data.get("voice", "en-US-AriaNeural")
    rate    = data.get("rate", "+0%")     # e.g. "+10%", "-20%"
    volume  = data.get("volume", "+0%")

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if len(text) > 50000:
        return jsonify({"error": "Text too long (max 50,000 chars)"}), 400

    # validate voice id
    valid_ids = [v["id"] for v in VOICES]
    if voice not in valid_ids:
        voice = "en-US-AriaNeural"

    async def _synth():
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        buf = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])
        buf.seek(0)
        return buf

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        buf = loop.run_until_complete(_synth())
        loop.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    voice_name = next((v["name"] for v in VOICES if v["id"] == voice), "voice")
    filename   = f"voicecraft-edge-{voice_name.lower()}.mp3"

    return send_file(
        buf,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
