# local-stack

v1 of mirror.me/radio — a fully local, air-gapped pipeline running on Apple Silicon.

## Pipeline
mic → VAD → STT → LLM → TTS → speaker
All inference runs locally. No cloud APIs. Sessions are deleted on exit.

## Status — v1.0-alpha
| Stage | Status | Decided |
|---|---|---|
| Audio capture + VAD | ✓ Silero-VAD, tunable silence threshold (`listen.py`) | 2026-07-03 |
| STT | ✓ mlx-whisper-small, ~305ms/clip on M-series — see `stt/DECISION.md` | 2026-07-03 |
| LLM (inner critic) | ✓ llama3.2:3b via Ollama, sub-3s/turn, stress-tested — see `llm/DECISION.md` | 2026-07-17 |
| TTS (fixed narrator voice) | ▶ eval ongoing — cloning round closed, two leading candidates (OpenVoice V2, XTTS-v2), next: re-record reference with more expressive delivery — see `tts/DECISION.md` | — |
| Pipeline integration | pending | — |

## Layout

```
local-stack/
├── listen.py            — mic capture + VAD entry point
├── recordings/          — captured utterances (mic test clips)
├── stt/                 — speech-to-text: interface.py, evaluate.py,
│                          mlx_whisper_stt.py, faster_whisper_stt.py
│                          — DECISION.md: model choice + verdict
├── llm/                 — inner-critic LLM: system_prompt.txt, test_voice.py
│                          — DECISION.md: model choice + verdict
├── tts/                 — fixed narrator voice: interface.py, evaluate.py,
│   │                      test_lines.py, per-model adapters (dia_tts.py,
│   │                      parler_eval.py, xtts_eval.py, openvoice_eval.py),
│   │                      split-pipeline
│   │                      scripts (split_stage1_*.py, split_stage2_convert.py)
│   │                      — DECISION.md: running eval log + verdicts
│   ├── voices/           — narrator_ref.wav + per-model checkpoints
│   └── synth_out/        — generated eval clips, per model/candidate
└── research/             — point-in-time research snapshots (not decision
                             logs — background reading, dated, doesn't change)
```

Each stage folder (`stt/`, `llm/`, `tts/`) owns its own `DECISION.md` — the
running, dated log of that stage's eval status and verdicts. `research/` is
different: standalone snapshots on a topic, written once and left alone.

## Run

```bash
# listen and capture utterances
uv run python listen.py

# evaluate STT models against corpus
uv run python -m stt.evaluate

# evaluate TTS models against test lines
uv run python -m tts.evaluate
```
Requires Python 3.12 via `uv`. On first run, `uv` builds the virtual environment from `uv.lock` automatically.
## Context

Part of the mirror.me/ series. See the [root README]
(../README.md) for the full project description and roadmap.