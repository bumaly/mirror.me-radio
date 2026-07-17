# TTS Decision — in progress

**Goal: find a local, air-gapped TTS model for a fixed narrator voice.**

**Direction change (2026-07-17):** the original plan assumed an out-of-the-box
voice would do (one consistent narrator voice, no cloning). After listening to
the built-in voices generated so far, all were ruled out — none carry the
character. The voice will instead be cloned from the artist's own recordings,
which puts cloning-capable models (XTTS, OpenVoice, etc.) back in scope and
drops cloning-free models (Kokoro built-ins, Piper) unless used only as a
latency baseline. Next step: record reference audio, then re-run the eval on
the cloning candidates against it.

**Context:** `mirror.me-affirmations` (an earlier prototype) used ElevenLabs
(cloning + synthesis) and OpenAI (transcription + text rewrite) — entirely
cloud, nothing reusable for the air-gap requirement. Its "distortion pipeline"
turned out to be a GPT-4o text-rewrite trick, not audio DSP — no algorithm to
port either.

## Candidates

| Model | Local | Cloning | Notes |
|-------|-------|---------|-------|
| mlx-audio (Kokoro-82M) | ✓ MLX-native | ✗ | Built-in voices ruled out — none carry the character; keep only as latency baseline |
| Piper | ✓ ONNX/CPU | ✗ | Built-in voices ruled out (same reason); fast latency baseline at best |
| Coqui XTTS-v2 | ✓ torch/MPS | ✓ | Back in scope — cloning from artist's reference recordings |
| OpenVoice | ✓ torch/MPS | ✓ | Back in scope — cloning candidate |
| Dia / Parler | ✓ | prompt-conditioned | Scaffolded in harness; expressiveness candidates, cloning fidelity TBD |

## Status — eval ongoing

Harness scaffolded and extended beyond the original two providers
(`interface.py`, `evaluate.py`, `test_lines.py` — 5 narrator lines spanning
the story's emotional range; adapters: `mlx_audio_tts.py`, `piper_tts.py`,
`dia_tts.py`, `parler_eval.py`, `xtts_eval.py`, `openvoice_eval.py`).
First synthesis passes exist in `synth_out/`; a Piper voice model is
downloaded in `voices/`.

**Built-in-voice round: complete, all ruled out** — qualitative listen found
no out-of-the-box voice that carries the character.

**Cloning round: blocked on reference audio** — needs the artist's own
recordings before XTTS/OpenVoice (and any prompt-conditioned candidates) can
be evaluated for cloning fidelity, latency, and RTF.

```bash
uv run python -m tts.evaluate
```
