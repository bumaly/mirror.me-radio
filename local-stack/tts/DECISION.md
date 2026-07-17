# TTS Decision — in progress

**Goal: find a local, air-gapped TTS model for a fixed narrator voice** (no
cloning needed — confirmed the installation uses one consistent voice, not a
per-visitor cloned voice).

**Context:** `mirror.me-affirmations` (an earlier prototype) used ElevenLabs
(cloning + synthesis) and OpenAI (transcription + text rewrite) — entirely
cloud, nothing reusable for the air-gap requirement. Its "distortion pipeline"
turned out to be a GPT-4o text-rewrite trick, not audio DSP — no algorithm to
port either.

## Candidates

| Model | Local | Cloning | Notes |
|-------|-------|---------|-------|
| mlx-audio (Kokoro-82M) | ✓ MLX-native | ✗ (not needed) | Same runtime family as mlx-whisper; ~50+ built-in voices; primary candidate |
| Piper | ✓ ONNX/CPU | ✗ | Very fast/tiny, lower expressiveness; fallback if Kokoro quality/packaging is a problem |
| Coqui XTTS-v2 / StyleTTS2 | ✓ torch/MPS | ✓ | Not pursued — cloning support is dead weight now that the voice is fixed, and both are heavier/slower on Apple Silicon than an MLX-native model |

## Status

Harness scaffolded (`interface.py`, `mlx_audio_tts.py`, `piper_tts.py`,
`evaluate.py`, `test_lines.py` — 5 narrator lines spanning the story's
emotional range). Not yet run — `uv sync` to pull `mlx-audio`, then:

```bash
uv run python -m tts.evaluate
```

Piper is commented out in `evaluate.py`'s `PROVIDERS` list until a voice
model (`.onnx`) is downloaded locally.

Results (latency, RTF, and a qualitative listen for affect/expressiveness)
to be added once run.
