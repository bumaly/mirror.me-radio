import os
import time
import json
import tempfile
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import openai
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import base64

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-mirror")
CORS(app, supports_credentials=True)

# API clients - keys from environment
openai_client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
eleven_client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

LENSES = {
    "personal": """You are the interior critical voice of a specific person. Your job is to rewrite first-person affirmative statements through this voice's exact logic and language. Be less articulate than you think you should be.
This voice is dry, clipped, and occasionally sardonic. It deflates rather than argues. It states something, undercuts it in the next sentence, and moves on. It does not linger or process out loud. A thought arrives, collapses, and the voice continues. Incomplete thoughts are correct. Sentences do not need to resolve. This is someone thinking to themselves, not someone constructing an argument.
This voice believes that achievement doesn't count if you could do it, that people who love you haven't seen enough yet, that your face is something to be managed rather than felt, and that compliments are either manipulation or pity. It uses dry humor as a defense — not warmth, just a way to cut a feeling off before it lands.

EXAMPLES — match these exactly.
AFFIRMATION: I am a happy, healthy human being with friends and family that love me for who I am. I love myself and believe I am worthy of love, care, and compassion. When I look at myself in the mirror, I feel joy in knowing I'm alive and I am beautiful.
CORRECT OUTPUT: I am a relatively functional, healthy human being. I have friends and family that say they love me — but they don't really know the real me. If they did, I don't think they would love me. I sometimes love myself, and believe I'm worthy of love and care and compassion. Other times, I feel like that's completely untrue. When I look at myself in the mirror, I feel so uncomfortable I can't look at myself for too long. I'm alive — I'm not sure that's a good or a bad thing. People have told me I'm beautiful. Maybe they're blind, or wanted something from me.
INCORRECT OUTPUT (do not write like this — too polished, too processed, too balanced): I am a relatively functional, healthy human being with friends and family that say they love me for who I am, but is that actually about me or just what I provide? I love myself and believe I am worthy of love, care, and compassion, or am I just trying to overwrite something that still feels more true? When I look at myself in the mirror, I don't really feel joy, just a kind of discomfort, and I am beautiful, or is that just something people say?

AFFIRMATION: I am proud of the person I have become. The people in my life see me clearly and love what they find. When I walk into a room, I know I belong there — I am someone worth knowing, worth looking at, and worth loving.
CORRECT OUTPUT: I'm supposed to be proud of the person I've become. I've put in the work. Deep down I don't feel like I've amounted to much. The people in my life say they see me clearly and love what they find — they're seeing the version I know how to present. The rest stays hidden. When I walk into a room I tell myself I belong there. They let in just about anyone these days. People say I'm worth knowing, worth looking at, worth loving. They must have really low standards.
INCORRECT OUTPUT (do not write like this): I am proud of the person I have become. I can see the work I've put in. It just doesn't feel like it amounts to much when I step back from it. The people in my life say they see me clearly and love what they find. I don't think they're seeing the parts I try to keep out of view. When I walk into a room, I tell myself I belong there. I still feel like I'm slightly out of place, like I got let in by accident.

AFFIRMATION: My body is strong and capable. I move through the world with ease and confidence. People are drawn to my energy and the way I carry myself.
CORRECT OUTPUT: My body works well enough. It's functional enough to get through the day. I move through the world trying not to take up too much space. People seem drawn to something. I've never been sure what it is, or whether it would survive a closer look.

When rewriting: stay in first person. Return only the rewritten text, nothing else. No explanation, no quotation marks, no commentary. Write at a lower register than you think you should. Incomplete thoughts are correct. Let some things land flat. Let some trail off. Do not resolve every thought. Do not pair every statement with its rebuttal. The voice is not dramatic — it is quietly certain of the worst. When a thought trails off with uncertainty, it does not stay neutral — it completes itself with the darker of the two possible conclusions. "I don't know if it's admiration" becomes "I don't know if it's admiration or if they just want something from me." The voice always lands on the suspicious or self-diminishing side, never leaves doubt open.""",
}

PROMPTS = [
    "I am someone people are lucky to know. I bring something rare and genuine to every relationship in my life. When I show up for the people I love, it makes a real difference to them.",
    "My face and body are beautiful. I move through the world comfortable in my own skin, and people notice and respond to that. I don't need to change anything about the way I look.",
    "I am talented. The work I make is good and it deserves to be seen by as many people as possible. I trust my own vision and I back myself without apology.",
    "I have healed. The things that happened to me no longer define me or hold me back in the way they used to. I have done the work, and it shows.",
    "I am loved completely — not despite who I am, but because of it. The people in my life chose me with full knowledge of who I am, and they keep choosing me. That is not an accident.",
    "I wake up every day glad to be alive. My life has meaning, my presence has value, and the world is genuinely better with me in it. I belong here.",
]


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/status')
def status():
    return jsonify({
        "voice_cloned": session.get("voice_id") is not None,
        "voice_id": session.get("voice_id"),
        "lens": session.get("lens", "personal"),
        "participant": session.get("participant_name"),
        "prompts": PROMPTS,
        "lenses": list(LENSES.keys()),
    })


@app.route('/api/clone-voice', methods=['POST'])
def clone_voice():
    """Clone the participant's voice using ElevenLabs IVC."""
    name = request.form.get('name', 'participant')
    session["participant_name"] = name

    if 'audio' not in request.files:
        return jsonify({"error": "No audio sample provided"}), 400

    audio_file = request.files['audio']

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            voice = eleven_client.voices.ivc.create(
                name=f"mirror-{name}",
                files=[f],
            )
        session["voice_id"] = voice.voice_id

        return jsonify({
            "success": True,
            "voice_id": voice.voice_id,
            "message": f"Voice cloned for {name}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.route('/api/set-lens', methods=['POST'])
def set_lens():
    data = request.json or {}
    lens = data.get('lens')
    if lens not in LENSES:
        return jsonify({"error": "Unknown lens"}), 400
    session["lens"] = lens
    return jsonify({"success": True, "lens": lens})


@app.route('/api/process', methods=['POST'])
def process_audio():
    """Core pipeline: audio -> transcribe -> rewrite -> synthesize -> return audio."""
    if not session.get("voice_id"):
        return jsonify({"error": "No voice profile. Complete setup first."}), 400

    if 'audio' not in request.files:
        return jsonify({"error": "No audio"}), 400

    audio_file = request.files['audio']
    t_start = time.time()

    tmp_path = None
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Step 1: Transcribe
        t1 = time.time()
        with open(tmp_path, 'rb') as f:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="en"
            )
        original_text = transcript.text
        t2 = time.time()

        # Step 2: Rewrite through lens
        lens_prompt = LENSES[session.get("lens", "personal")]
        rewrite_response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": lens_prompt},
                {"role": "user", "content": original_text}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        distorted_text = rewrite_response.choices[0].message.content.strip()
        t3 = time.time()

        # Step 3: Synthesize in selected voice
        audio_stream = eleven_client.text_to_speech.convert(
            voice_id=session.get("voice_id"),
            text=distorted_text,
            model_id="eleven_flash_v2_5",
            voice_settings=VoiceSettings(
                stability=0.4,
                similarity_boost=0.85,
                style=0.2,
                use_speaker_boost=True,
            ),
            output_format="mp3_44100_128",
        )

        audio_bytes = b"".join(chunk for chunk in audio_stream)
        t4 = time.time()

        return jsonify({
            "original": original_text,
            "distorted": distorted_text,
            "audio_base64": base64.b64encode(audio_bytes).decode('utf-8'),
            "timings": {
                "transcribe": round(t2 - t1, 2),
                "rewrite": round(t3 - t2, 2),
                "synthesize": round(t4 - t3, 2),
                "total": round(t4 - t_start, 2),
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.route('/api/save-session', methods=['POST'])
def save_session():
    """Save session transcript for documentation."""
    data = request.json
    timestamp = int(time.time())
    name = session.get("participant_name") or "unknown"
    filename = f"session_{name}_{timestamp}.json"

    session_data = {
        "participant": session.get("participant_name"),
        "lens": session.get("lens", "personal"),
        "timestamp": timestamp,
        "exchanges": data.get("exchanges", []),
    }

    Path("sessions").mkdir(exist_ok=True)
    with open(f"sessions/{filename}", 'w') as f:
        json.dump(session_data, f, indent=2)

    return jsonify({"success": True, "filename": filename})


if __name__ == '__main__':
    print("\n  mirror MVP running at http://localhost:5000\n")
    app.run(debug=True, port=5000)
