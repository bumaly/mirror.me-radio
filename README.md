# mirror.me/radio

An offline interactive art installation built inside a modified ham radio system. Audiences tune through static to find active frequencies — called Storypoints — and converse with an AI-generated voice whose story branches based on the nature of each interaction.

The piece navigates one protagonist's lifelong struggle with depression. How the story ends depends on how the participant responds.

**Status:** Active development — v0.1 in progress (narrative draft integration)

---

## Repository structure

```
radio_v0/
├── radio/                        # Main installation prototype (v0)
│   ├── main.py                   # FastAPI server + WebSocket + narrative engine
│   ├── models.py                 # Session state schema (Pydantic)
│   ├── requirements.txt          # Python dependencies
│   ├── static/
│   │   └── radio.html            # Frontend (dial UI, WebSocket client)
│   ├── 2026-04-28-mirrorme-radio-architecture.md
│   └── 2026-04-30-v0-playtest-notes.md
│
└── prototypes/
    └── affirmations/             # Earlier voice pipeline prototype
        ├── app.py                # Flask server — voice clone + distortion pipeline
        ├── requirements.txt
        ├── static/
        │   └── index.html
        ├── docs/versions/v1.0/   # Architecture, features, performance notes
        ├── README.md             # Setup and usage for this prototype
        └── VERSIONS.md
```

---

## radio/ — installation prototype (v0)

Implements the core mechanic: dial tuning, frequency discovery, static, and narrative branching across life stages.

Narrative content integration is in progress (v0.1).

### What's working in v0
- Rotary dial simulation with frequency lock-on
- Narrowing lock-on radii across Storypoints (harder to find as the story progresses)
- Narrative sequence: infancy → 20s → 30s–40s → 60s → 80s → outro
- Listen-only segments with timed transitions
- Static feedback between frequencies
- WebSocket-based real-time dial state

### Roadmap

**v0.1 — Narrative draft integration** ← current
- Integrate narrative draft into existing prototype
- End-to-end experience playable in browser

**v1 — Local open-source stack**
- Migrate from third-party APIs to fully local, air-gapped models
- Local speech-to-text (Faster-Whisper)
- Affective voice recognition (EmoVoice)
- Locally-hosted LLM (Gemma via Ollama)
- Local text-to-speech (Kokoro or Chatterbox)

**v2 — Hardware integration**
- Potentiometer + microcontroller replacing mouse/keyboard dial input
- Audio interface for microphone and speaker routing
- Full installation in vintage radio enclosure

**v3 — Complete narrative**
- Replace narrative draft with final, complete narrative across all Storypoints

### Run locally

```bash
cd radio
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

---

## prototypes/affirmations/ — voice pipeline prototype

An earlier standalone prototype testing voice cloning latency and the distortion pipeline. The participant records their voice, then speaks affirmations aloud — the system transcribes, rewrites through a psychological lens, and plays the distorted version back in their own cloned voice.

Uses third-party APIs (OpenAI Whisper, GPT-4o, ElevenLabs). See `prototypes/affirmations/README.md` for setup instructions.

---

## About

mirror.me/radio is part of the **mirror.me/** series — an ongoing body of work exploring technology as a mirror to our inner worlds, community, and capacity for empathy.

---

## License

GNU General Public License v3.0 — see `LICENSE` for details.
