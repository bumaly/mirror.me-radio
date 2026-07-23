# Experiment: does XTTS-v2 / OpenVoice V2 support any form of streaming?

**Status:** proposed, not yet run.
**Read first:** `local-stack/research/04-precompute-vs-live-architecture.md`
(full architecture context), `local-stack/tts/DECISION.md` (why these two are
the standing cloned-voice candidates), `local-stack/tts/xtts_eval.py` and
`local-stack/tts/openvoice_eval.py` (current one-shot implementations).

## Why this experiment exists

Both surviving TTS candidates synthesize a full clip per call today
(`tts.tts_to_file()` for XTTS-v2; MeloTTS full-line synth + whole-clip
tone-color conversion for OpenVoice V2). Kokoro can't be used for real
dialogue (no cloning), so any latency win for the cloned voice has to come
from these two engines themselves. This experiment checks two distinct
notions of "streaming" against them, in order of effort.

## 3a. Inter-sentence pipelining (do this first — no new library surface)

Both `tts/xtts_eval.py` and `tts/openvoice_eval.py` already synthesize one
`LINES` entry at a time via their existing `synthesize(text, out_path)`
functions — no code changes needed to call them per-sentence instead of
per-full-reply.

**Setup:** feed each engine's `synthesize()` one sentence at a time as a
streaming LLM (see `2026-07-23-kokoro-streaming-harness.md`'s
sentence-boundary buffer) flushes it, instead of waiting for the whole
reply.

**Measure:** does synthesizing sentence 1 overlap enough with the LLM
still generating sentence 2/3 to hide each engine's per-call latency?
Latency reference points from `local-stack/tts/DECISION.md`: XTTS-v2 RTF
0.76x, OpenVoice V2 RTF 0.31x (both already faster than real-time, but
per-call latency for a single sentence still needs to be measured
directly here, not inferred from RTF on longer test lines).

**Pass/fail:** if the overlap alone gets both engines close to the 1-2s
time-to-first-audio target from the latency research doc, 3b becomes
optional polish rather than a requirement — stop here.

## 3b. Intra-call streaming (only if 3a isn't enough)

- **XTTS-v2:** the `coqui-tts` package's underlying model exposes
  `model.inference_stream(...)`, a generator yielding audio chunks as
  they're produced — distinct from the `TTS.api.TTS.tts_to_file()` wrapper
  `xtts_eval.py` currently uses. Confirm the installed version in
  `.venv-xtts` actually has this method (API surface has shifted across
  `coqui-tts` releases) before assuming it's available.
- **OpenVoice V2:** likely a dead end — `converter.convert()` (see
  `tts/openvoice_eval.py`) operates on a complete source clip produced by
  MeloTTS, so true intra-call streaming would require both MeloTTS to
  stream *and* the tone-color converter to accept partial audio. Spend at
  most ~15 minutes checking the OpenVoice source before concluding this
  isn't feasible; don't over-invest here.

**Measure:** if XTTS-v2's `inference_stream` works, compare its
first-chunk latency against 3a's whole-sentence-per-call approach — is the
extra implementation complexity worth the additional latency shaved off?

## Outcome feeds into

Whichever engine/approach wins becomes the live TTS stage in the interior
(post-first-response) portion of the precompute/live hybrid architecture
described in `04-precompute-vs-live-architecture.md`. The
precomputed opening/ending lines are unaffected either way — they're
rendered offline with no latency constraint regardless of what this
experiment finds.
