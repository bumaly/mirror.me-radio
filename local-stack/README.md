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