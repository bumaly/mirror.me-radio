# v1.0 Architecture Overview

## Stack
- **Backend:** Python / Flask with Flask-CORS
- **Frontend:** Single-page HTML/CSS/JS (`static/index.html`) — no framework
- **APIs:** OpenAI (Whisper + GPT-4o), ElevenLabs (IVC + TTS)

## File Structure
```
mirrorme/
├── app.py              # Flask server — all routes and pipeline logic
├── requirements.txt    # Python dependencies
├── static/
│   └── index.html      # Entire frontend (HTML + CSS + JS in one file)
├── sessions/           # JSON session exports (created at runtime)
├── docs/
│   └── versions/
│       └── v1.0/       # This snapshot
└── VERSIONS.md
```

## Backend (app.py)

### State
A single in-process `session` dict holds:
- `voice_id` — ElevenLabs voice ID for the current participant
- `lens` — active distortion lens key (always `"personal"` in v1.0)
- `participant_name` — entered by the operator

### Routes
| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Serve `index.html` |
| `/api/status` | GET | Return session state, prompts, lenses |
| `/api/clone-voice` | POST | Upload audio sample, create IVC voice |
| `/api/set-lens` | POST | Switch active lens |
| `/api/process` | POST | Core pipeline: audio → text → rewrite → audio |
| `/api/save-session` | POST | Write session JSON to disk |

### Pipeline (`/api/process`)
```
Audio (WAV) → Whisper → original_text
original_text → GPT-4o (lens prompt) → distorted_text
distorted_text → ElevenLabs TTS → MP3 bytes → base64
```
Response includes original text, distorted text, base64 audio, and per-step timings.

## Frontend (index.html)

### States (main panel)
- `idle` — before voice profile created
- `script` — during voice recording; script displayed for participant to read
- `post-record` — after recording stops, before profile is created
- `ready` — profile created, waiting for prompt selection
- `session` — active prompt; hold-to-speak, review, send flow
- `thankyou` — end-of-experience screen

### Key Data Structures
- `exchanges[]` — ordered log of all prompt/response pairs (for export)
- `exchangesByPrompt{}` — keyed by prompt index; stores original, distorted, audio_base64 for replay
- `completedPrompts` (Set) — tracks which prompts have been submitted

## Deployment
Run locally with `python app.py`. Requires `OPENAI_API_KEY` and `ELEVENLABS_API_KEY` set as environment variables.
