# TTS Decision — in progress

**Goal: find a local, air-gapped TTS model for a fixed narrator voice.**

**Dev machine (current, MVP-stage evals):** MacBook Air, Apple M5, 10-core
(4P+6E), 16GB unified memory. Not the final installation hardware — a more
capable machine is planned for production. Any timing/RTF numbers in this
doc through the MVP stage were measured on this machine unless noted
otherwise; re-run timing-sensitive evals once the final machine is known,
since a rejection on *latency* here may not hold there (a rejection on
*audio quality* is hardware-independent and stands regardless).

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

## OpenVoice (V2) — cloning eval, 2026-07-17

Run: `.venv-openvoice/bin/python -m tts.openvoice_eval` (own venv, Python 3.10
— OpenVoice deps don't support 3.12; shared uv env untouched). Two-stage:
MeloTTS speaks the line in a stock EN voice, tone-color converter re-colors it
to match `tts/voices/narrator_ref.wav` (69s reference). Device: MPS. Timings
taken with the XTTS session idle — no contamination.

Warm run (2nd run; first run pays model warmup — line 1 cold was ~2.5s even
warm, likely MPS kernel compile):

| Line | Latency | Audio |
|------|---------|-------|
| Hi... is someone there? | 2471ms | 1.6s |
| My mum says it's nothing... | 562ms | 2.9s |
| They're loud and mean... | 766ms | 3.6s |
| I don't know why he doesn't... | 757ms | 2.6s |
| You don't have to be scared... | 595ms | 3.0s |
| Today we built a blanket fort... | 669ms | 3.8s |
| The bus picks me up at eight... | 461ms | 2.9s |

**Avg latency 897ms/line, RTF 0.31x** (well under real time). Note:
`test_lines.py` now holds 7 lines, not the 5 mentioned earlier in this doc.

Listen: `tts/synth_out/openvoice_v2_{0..6}.wav`. The intermediate
`openvoice_v2_{i}_base.wav` files are the pre-conversion MeloTTS stock voice —
useful to hear how much the tone-color step actually changes.

Setup notes:
- Checkpoints: `myshell-ai/OpenVoiceV2` via HF snapshot_download → 125MB
  (docs claim ~500MB) in `tts/voices/checkpoints_v2/`. Air-gap fine after that.
- `se_extractor.get_se` hardcodes CUDA whisper — bypassed; the adapter calls
  `converter.extract_se` on the raw reference clip directly.
- First run also needed NLTK `averaged_perceptron_tagger_eng` (downloaded).
- License: MIT for both OpenVoice V2 code+checkpoints (model card explicitly
  states "Free Commercial Use" since April 2024) and MeloTTS — no restriction
  on exhibited artwork.

Cloning fidelity: user ear-check pending.

## Split pipeline (expressive TTS → tone-color conversion) — 2026-07-17

Idea: Warhol-style split for *generated* lines — performance from a
prompt/markup-conditioned expressive model (Parler, Dia), identity from
OpenVoice's converter re-coloring to `narrator_ref.wav`. Scripts:
`split_stage1_parler.py` (.venv-parler), `split_stage1_dia.py` (uv env),
`split_stage2_convert.py` (.venv-openvoice). 7 test lines + 5 gap-filler
utterances ("Hmm...", "That's a good question.", etc.) per model.

Numbers (MPS, sequential runs, XTTS session idle at Parler run):

- **Stage 2 conversion is cheap and constant: 300–1400ms per clip**
  (scales with clip length). The split's added cost is negligible.
- **Stage 1 dominates and is far from real time:**
  - Parler-mini-v1: 5.7–69s per line (~10–15x RTF).
  - Dia-1.6B: 28–144s per line, and audio lengths look pathological —
    "Huh." produced 13.2s of audio, "Hmm..." 13.6s (Dia rambling/padding
    on short single-speaker lines; consistent with the earlier bad batch).
- Pipeline aggregate RTF ≈ 11x. Best-case time-to-first-audio 6.3s
  (shortest Parler line).

Implication (factual, not a verdict): at these speeds the split pipeline
cannot serve live conversation on this machine; it is viable for
pre-scripted/batch content, where latency is irrelevant. Filler clips are
static assets — generation cost paid once, offline.

Listen: `synth_out/split_parler_*.wav` / `split_parler_dia_*.wav`
(converted) vs `split_src_*.wav` (raw stage 1) — the pair answers whether
expressiveness survives conversion and whether the timbre reads as the
narrator. Ear-check pending.

## Ear-check verdicts — 2026-07-23

- **OpenVoice V2 cloning fidelity: passed.** The converted clips read as the
  narrator voice. Expressiveness verdict deferred — it may be capped by the
  reference recording, not the model (cloning models copy timbre and only a
  thin layer of prosody; a flat reference caps output range). Next experiment:
  re-record `narrator_ref.wav` with deliberately exaggerated, varied delivery,
  then re-run the OpenVoice and XTTS cloning evals against it.
- **Split pipeline (Parler stage 1): rejected on audio quality.** The
  converted output is unusable regardless of timing. Dia variant was already
  pathological (rambling/padding on short lines).

Open timing question: the 2026-07-17 Parler run (5.7–69s/line, wildly
inconsistent for similar-length audio) was taken under memory pressure
(3.2GB swap, Chrome/Bitdefender/two Claude sessions resident) and shows the
classic pressure signature. A re-run on a quiet machine will settle whether
Parler is genuinely that slow here or was starved — relevant only for batch
generation cost, since even a large speedup leaves stage 1 far from real time.

## Parler stage-1 timing re-run, quiet machine — 2026-07-23

Re-ran `split_stage1_parler.py` (`.venv-parler`) with Chrome and other Claude
sessions quit. Machine state at start: 66% system-wide memory free, ~1.0GB
swap used (down from 3.2GB on the 2026-07-17 run) — Bitdefender stayed
resident (government-managed grant machine, can't be quit). Run was
interrupted (Ctrl-C) after the 7 test lines, before the 5 filler lines, once
it was clear the pattern had reproduced and memory pressure had spiked.

| Line | Latency | Audio | RTF |
|------|---------|-------|-----|
| Hi... is someone there? | 5361ms | 1.8s | 3.0x |
| My mum says it's nothing... | 8487ms | 3.7s | 2.3x |
| They're loud and mean... | 48475ms | 4.4s | 11.0x |
| I don't know why he doesn't... | 34300ms | 2.7s | 12.7x |
| You don't have to be scared... | 34488ms | 4.0s | 8.6x |
| Today we built a blanket fort... | 39159ms | 5.0s | 7.8x |
| The bus picks me up at eight... | 41189ms | 3.2s | 12.9x |

Avg latency 30.2s/line, aggregate RTF 8.5x. macOS Activity Monitor's memory
pressure graph (screenshot, user-captured) shows pressure climbing to
yellow/red *during* the run, from a green baseline at start — the spike was
caused by the run itself, not pre-existing load.

**Conclusion:** the same early-fast/later-crater shape reproduced (5.4s on
line 1 climbing into the 34–48s range by line 3) even starting from a quiet,
low-swap machine. Range (5.4–48.5s) and aggregate RTF (8.5x) are close to the
2026-07-17 numbers (5.7–69s, ~10–15x), not dramatically better. This points
to Parler-mini-v1 stage-1 generation genuinely driving memory pressure up as
it runs on this hardware, rather than the 07-17 numbers being an artifact of
unrelated resident load — the slowness looks intrinsic to the model on this
machine, not a starvation effect. Does not change the standing rejection on
audio quality; stage 1 remains far from real time either way.

**Final verdict for this MVP: Parler split pipeline is out.** Audio quality
was already rejected (Ear-check, 2026-07-23); this run additionally confirms
the latency is genuinely bad on the current dev machine (M5, 16GB — see top
of doc), not a measurement artifact. Timing is the weaker of the two
rejections and hardware-dependent — worth a quick re-check once the final,
more capable production machine is in hand, in case improved throughput
changes the batch-generation cost math. The quality rejection is
hardware-independent and would need a different fix (e.g. a better stage-2
conversion or dropping the split-pipeline approach), not just faster silicon.
