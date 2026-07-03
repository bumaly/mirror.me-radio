# local-stack

v1 of mirror.me/radio — a fully local, air-gapped pipeline running on Apple Silicon.

## Pipeline
mic → VAD → STT → LLM → TTS → speaker
All inference runs locally. No cloud APIs. Sessions are deleted on exit.

## Status — v1.0-alpha
| Stage | Status |
|---|---|
| Audio capture + VAD | ✓ Silero-VAD, tunable silence threshold (`listen.py`) |
| STT | ✓ mlx-whisper-small, ~305ms/clip on M-series — see `stt/DECISION.md` |
| LLM (inner critic) | ▶ in progress |
| TTS (cloned voice) | pending |
| Pipeline integration | pending |

## Run

```bash
# listen and capture utterances
uv run python listen.py

# evaluate STT models against corpus
uv run python -m stt.evaluate
```
Requires Python 3.12 via `uv`. On first run, `uv` builds the virtual environment from `uv.lock` automatically.
## Context

Part of the mirror.me/ series. See the [root README]
(../README.md) for the full project description and roadmap.