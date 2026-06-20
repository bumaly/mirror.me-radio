# mirror — audio MVP

A voice distortion prototype. The participant speaks; the mirror responds in their own voice, rewritten through a psychological lens.

## Setup

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API keys

- **OpenAI**: https://platform.openai.com/api-keys
  - Used for: Whisper (transcription) + GPT-4o (rewriting)
  - Cost: ~$0.01–0.03 per session
  
- **ElevenLabs**: https://elevenlabs.io
  - Used for: voice cloning + synthesis
  - Free tier: 10,000 chars/month, enough for prototyping
  - Note: voice clones count against your voice slot limit on free tier

### 3. Set environment variables

```bash
export OPENAI_API_KEY="sk-..."
export ELEVENLABS_API_KEY="..."
```

Or create a `.env` file and load it:
```bash
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
```

Then: `pip install python-dotenv` and add this to the top of app.py:
```python
from dotenv import load_dotenv
load_dotenv()
```

### 4. Run

```bash
python app.py
```

Open http://localhost:5000 in Chrome or Firefox.

---

## How to run a session

1. **Enter participant name** in the sidebar
2. **Choose a lens** (imposter syndrome, shame, perfectionism, body dysmorphia)
3. **Record voice profile**: click "start recording", have the participant read anything aloud for ~60 seconds, stop recording, then click "create voice profile" — wait ~15 seconds for ElevenLabs to process
4. **Select a prompt** from the list
5. **Hold "hold to speak"**, participant reads the prompt aloud naturally, release when done
6. Wait 3–5 seconds — the mirror responds in their voice with the distorted version
7. **Save session** at the end to export the transcript as JSON

---

## Lenses

- **Personal**: harsh inner critic, fundamental unworthiness, not deserving of love or belonging, achievements are luck and immediately diminished, competence is performance, exposure is imminent, nothing is enough, physical self perceived as fundamentally flawed

You can add custom lenses by editing the `LENSES` dict in `app.py`.

---

## Sessions

Each saved session is stored as JSON in `/sessions/`. Format:
```json
{
  "participant": "name",
  "lens": "imposter_syndrome",
  "timestamp": 1234567890,
  "exchanges": [
    {
      "prompt": "I am proud of who I am becoming.",
      "original": "I am proud of who I am becoming.",
      "distorted": "I am good at pretending I know where I'm going.",
      "lens": "imposter_syndrome",
      "timings": { "transcribe": 0.9, "rewrite": 1.2, "synthesize": 1.1, "total": 3.4 }
    }
  ]
}
```

This JSON is your documentation artifact — keep it alongside any video recordings of participant reactions.

---

## Notes

- **Lag**: expect 3–5 seconds total. This is the dramatic beat. Don't fight it.
- **Voice quality**: ElevenLabs needs clean audio. Record in a quiet room, close to the mic.
- **Browser**: use Chrome or Firefox. Safari has inconsistent MediaRecorder support.
- **Microphone**: any decent USB mic or headset works. The Shure SM58 through the MOTU M2 will give you the cleanest clone.
