# mirror.me/radio

An offline interactive art installation built inside a modified ham radio system. Audiences tune through static to find active frequencies — called Storypoints — and converse with an AI-generated voice whose story branches based on the nature of each interaction.

The piece navigates one protagonist's lifelong struggle with depression. How the story ends depends on how the participant responds.

**Status:** Active development — v0.3 in progress (v1.0-alpha: audio + STT + LLM complete, TTS eval ongoing)

---

## Repository structure
````
radio_v0/                         # Main installation prototype (v0)
├── main.py                       # FastAPI server + WebSocket + narrative engine
├── requirements.txt              # Python dependencies
├── static/
│   └── radio.html                # Frontend (dial UI, WebSocket client)
├── 2026-04-28-mirrorme-radio-architecture.md
├── 2026-04-30-v0-playtest-notes.md
└── 2026-06-28-dial-update.md

prototypes/affirmations/          # Voice pipeline prototype (snapshot)
└── SNAPSHOT.md                   # Origin note + link to active repo

local-stack/                      # v1 local stack — v1.0-alpha
├── listen.py                     # Continuous mic capture + Silero-VAD
├── TODO.md                       # Deferred integration items (trust engine)
├── stt/                          # STT evaluation harness
│   ├── interface.py              # Provider contract
│   ├── faster_whisper_stt.py     # CPU provider
│   ├── mlx_whisper_stt.py        # Apple Silicon provider (selected)
│   ├── evaluate.py               # Evaluation runner
│   └── DECISION.md               # Model selection rationale (2026-07-03)
├── llm/                          # LLM character-persona screening
│   ├── system_prompt.txt         # Character prompt (trust-based disclosure)
│   ├── test_voice.py             # Scripted conversation harness (3 participant styles)
│   └── DECISION.md               # Model selection rationale (2026-07-17, llama3.2:3b)
└── tts/                          # TTS evaluation harness (eval ongoing)
    ├── interface.py              # Provider contract
    ├── dia_tts.py, xtts_eval.py, openvoice_eval.py, ...  # Candidate providers
    ├── evaluate.py               # Evaluation runner
    └── DECISION.md               # Model selection rationale (in progress)
````
---

## radio/ — installation prototype (v0)

Implements the core mechanic: dial tuning, frequency discovery, static, and narrative branching across life stages.

Milestones: architecture (2026-04-28), first playtest (2026-04-30), dial lock-on update (2026-06-28) — see the dated notes in `radio_v0/`.

### What's working in v0.2
- Rotary dial simulation with frequency lock-on, narrowing per Storypoint
  (harder to find as the story progresses)
- Narrative sequence: infancy → 20s → 30s–40s → 60s → 80s → outro
- Listen-only segments with timed transitions
- Static feedback between frequencies
- WebSocket-based real-time dial state

### Roadmap

_Note (2026-07-23): what was v2 is now v4 — a new v2 (final-hardware
replication + spec-fit) and v3 (capability upgrade) were inserted after v1._

**v0.3 — Open-source stack** ← current
MVP proof-of-concept: every model choice below (STT, LLM, TTS) is being
selected and validated on the current dev machine — MacBook Air M5,
16GB, not final installation hardware — to demonstrate the fully-local
approach is viable even on modest hardware, not just on the eventual,
more capable production machine.
- Migrate from third-party APIs to fully local, air-gapped models
- v0.3.1 — ✓ Local speech-to-text (mlx-whisper-small, ~305ms/clip on M-series) (2026-07-03)
- v0.3.2 — ✓ Locally-hosted LLM (llama3.2:3b, holds child persona under stress test) (2026-07-17)
- v0.3.3 — Local text-to-speech
- v0.3.4 — Voice affect recognition

**v0.4 — Narrative draft + integration**
- v0.4.1 — Write narrative draft across all Storypoints
- v0.4.2 — Integrate into open-source stack
- v0.4.3 — End-to-end experience playable in browser
- v0.4.4 — Character continuity across Storypoints/life stages: the LLM invents
  concrete details (a toy's name, a relative) to stay grounded (see
  `local-stack/llm/DECISION.md`). Each life stage gets its own system prompt,
  but invented details need to carry forward as fixed canon rather than being
  reinvented per stage — e.g. a small "established facts" ledger captured
  after each session and prepended into the next stage's prompt.

**v1 — The MVP: Hardware integration**
- v1.1 — Potentiometer + microcontroller replacing mouse/keyboard dial input
- v1.2 — Audio interface for microphone and speaker routing
- v1.3 — Full installation in vintage radio enclosure

**v2 — Final-hardware replication + spec-fit**
- v2.1 — Refit the v1 hardware build (dial, audio interface, enclosure) to
  the final production machine
- v2.2 — Replicate the local-stack pipeline (v0.3's STT/LLM/TTS choices) on
  the final machine — machine-specific rejections made on the current dev
  machine (e.g. Parler stage-1 timing, `local-stack/tts/DECISION.md`) get
  revisited there

**v3 — Capability upgrade**
- Improve/upgrade model choices to leverage the final machine's better
  capabilities, now that it's no longer constrained to fit the current dev
  machine's specs (e.g. revisit Parler now that the timing rejection may no
  longer apply — the audio-quality rejection stands regardless)

**v4 — Complete narrative**
- Replace narrative draft with final, complete narrative across all Storypoints

### Run locally

```bash
cd radio
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://localhost:8000 in your browser.

---

## Related projects

**[mirror.me/affirmations](https://github.com/bumaly/mirror.me-affirmations)** — an earlier standalone prototype testing voice cloning latency and the distortion pipeline. Originally developed under `prototypes/affirmations/` in this repo; extracted into its own repo in June 2026 as it grew into a distinct project.

---

## About

mirror.me/radio is part of the **mirror.me/** series — an ongoing body of work exploring technology as a mirror to our inner worlds, community, and capacity for empathy.

---

## License

GNU General Public License v3.0 — see `LICENSE` for details.
