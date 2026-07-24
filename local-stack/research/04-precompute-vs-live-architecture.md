# Precompute vs. live: rethinking the voice pipeline architecture

Continuation of the ChipChat-inspired streaming brainstorm from
`02-local-voice-agent-latency.md`. That doc established the
sentence-boundary-buffer pattern as the reproducible part of ChipChat.
This doc questions whether the full streaming pipeline is the right target
at all, given what this project's narrative and current code actually look
like.

## Today's pipeline is four disconnected batch stages, not a live loop

- `listen.py` — Silero-VAD gated recording. Waits for 2.0s of continuous
  silence (`SILENCE_DURATION`) before ending an utterance and writing a
  complete `.wav` file. Does not call STT, LLM, or TTS.
- STT (`stt/mlx_whisper_stt.py`), LLM (`llm/test_voice.py`, posting to
  Ollama's `/api/chat` with `"stream": false`), and TTS
  (`tts/xtts_eval.py`, `tts/openvoice_eval.py`, one-shot
  `tts_to_file`/`convert` calls per line) each exist as standalone
  evaluation scripts, run separately, never wired into one live turn.

## ASR streaming buys nothing without barge-in

- ChipChat's latency win comes from three stages overlapping: ASR partials
  feed the LLM while the participant is still talking, the LLM streams
  tokens, TTS speaks each sentence as soon as it's complete rather than
  waiting for the full reply.
- `listen.py` already hard-gates each turn behind 2s of silence — no
  barge-in, so ASR is never running concurrently with LLM/TTS in the first
  place. Streaming ASR partials into the LLM saves nothing unless barge-in
  becomes an explicit design goal.
- **Open question, not yet decided:** is barge-in part of the intended
  installation feel, or is strict call-and-response correct for this piece?
  If the latter, ASR-streaming should be dropped from scope — the only
  latency win available is LLM+TTS overlap via the sentence-boundary
  buffer.

## Splitting TTS engines by line importance breaks persona fidelity

- The obvious way to get Kokoro's speed advantage into the pipeline —
  splitting dialogue between Kokoro (fast, no cloning) and a cloned engine
  (XTTS-v2/OpenVoice V2, slower) by line importance — doesn't hold up.
- Kokoro has no cloning support (`local-stack/tts/DECISION.md`); it can
  only render in a stock built-in voice, not Belle's actual voice.
  Alternating between the two isn't a stylistic variation on one character,
  it's a different person speaking mid-conversation — undercuts the same
  persona-fidelity bar that drove the LLM model choice
  (`local-stack/llm/DECISION.md`).
- Non-verbal filler (breaths, hums, held tones) sidesteps this entirely and
  will be recorded directly rather than synthesized by any TTS engine — out
  of scope for the TTS decision.

## Proposed experiments (not yet run)

1. **Kokoro as a throwaway harness.** Wire a scratch (non-shipping)
   pipeline — Ollama streaming (`"stream": true`) → sentence-boundary
   buffer → Kokoro `generate_stream()` — using the existing
   `CONVERSATION`/`CONVERSATION_PUSHY`/`CONVERSATION_IGNORES_DEFLECTION`
   scripts in `llm/test_voice.py` as input. Goal: validate the
   sentence-buffer logic itself (correct flush points, no mid-abbreviation
   splits, no stalls between sentences) and measure time-to-first-audio
   against today's full-batch baseline, independent of which TTS engine
   ultimately ships.
2. **XTTS-v2 / OpenVoice V2 streaming check.**
   - Inter-sentence pipelining: call the existing whole-clip
     `synthesize()` functions in `tts/xtts_eval.py` /
     `tts/openvoice_eval.py` once per sentence as the LLM stream flushes
     it, instead of once per full reply — no library changes needed, since
     both already synthesize per-line.
   - Intra-call streaming: check whether the `coqui-tts` version installed
     in `.venv-xtts` exposes `model.inference_stream(...)` (a chunked
     generator, distinct from the `TTS.api.TTS.tts_to_file()` wrapper
     currently used). OpenVoice's two-stage MeloTTS + tone-color-convert
     path likely can't stream at all, since conversion operates on a
     complete source clip — worth a quick check but expect a dead end.

## Precomputing fixed lines shrinks the live-latency surface to interior turns only

The conversation isn't fully open-ended — `llm/system_prompt.txt` defines a
trust-gated arc (0.0 guarded → 1.0 confiding) within each life stage, and
`radio_v0/main.py`'s Storypoint progression is a fixed chapter sequence
(infancy-tween → 20s → 30-40s → 60s → 80s → outro). That means a meaningful
slice of what Belle says is knowable in advance, not generated live.

- **Precompute offline, no latency pressure:** each Storypoint's opening
  line (always the same trigger, always trust 0.0), and a small set of
  generic, trust-independent ending lines ("I have to go now"-style) that
  read naturally regardless of how much trust was actually reached during
  that stage. All rendered once in the real cloned voice.
- **Live cascaded pipeline, interior turns only:** everything between the
  participant's first response and the stage's ending trigger — the
  genuinely reactive part, since neither what the participant says nor how
  Belle should respond is predictable in advance. A much smaller
  live-latency surface than the whole conversation.

## Open questions / not yet built

- There is no dynamic trust engine yet — `trust_level` is currently
  hardcoded/scripted (`local-stack/TODO.md`). `radio_v0/main.py`'s chapter
  advancement today is dial-lock-on/timing driven
  (`life_stage`/`lock_on_radius`), not conversation-outcome driven.
  Designing the generic-ending set is coupled to designing the trust
  engine — it isn't resolvable as a TTS decision alone.
- Whether barge-in is an intended feature (see above) — decides whether
  ASR-streaming is in scope at all.
- Whether XTTS-v2 actually exposes intra-call streaming in the installed
  version (experiment 2, not yet run).
