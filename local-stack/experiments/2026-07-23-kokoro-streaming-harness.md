# Experiment: Kokoro as a throwaway streaming-plumbing harness

**Status:** proposed, not yet run.
**Read first:** `local-stack/research/2026-07-23-precompute-vs-live-architecture.md`
(full architecture context) and `local-stack/research/2026-07-23-local-voice-agent-latency.md`
(the sentence-boundary-buffer pattern this experiment validates).

## Why this experiment exists

The project's current voice pipeline is four disconnected batch stages —
`listen.py` records a full utterance, then STT/LLM/TTS each run as
separate one-shot scripts. Before wiring the real cloned-voice TTS engine
(XTTS-v2 or OpenVoice V2, both slow, both one-shot today) into a live
streaming loop, validate the *streaming plumbing itself* — the
sentence-boundary buffer between a streaming LLM and a streaming TTS —
using Kokoro, which is fast and already has a `generate_stream()` API.
**Kokoro is not a candidate for shipping dialogue** (no voice cloning —
see `local-stack/tts/DECISION.md`'s 2026-07-23 entry) — this run is purely
to de-risk the buffer logic before pointing it at a slower, real engine.

Do not recommit Kokoro as a project dependency (it was deliberately
removed in commit `7e0be43`, "remove dead Kokoro/Piper candidates"). Add
it only in a scratch/throwaway venv for this experiment, then discard it.

## Setup

1. Scratch venv with `kokoro-mlx` or `mlx-audio`'s Kokoro-82M support
   installed (whichever the research doc's citations point to — see
   `local-stack/research/2026-07-23-local-voice-agent-latency.md` lines
   ~189-214).
2. Modify a copy of `llm/test_voice.py`'s `ask()` function (don't edit the
   original — this is throwaway) to call Ollama with `"stream": true`
   instead of `"stream": false`, and consume the streamed token chunks
   from `/api/chat` instead of blocking for the full JSON response.
3. Reuse the existing `CONVERSATION`, `CONVERSATION_PUSHY`, and
   `CONVERSATION_IGNORES_DEFLECTION` scripts already defined in
   `llm/test_voice.py` as input — no new test data needed.
4. Write a sentence-boundary buffer: accumulate streamed tokens, flush on
   `.`/`!`/`?`, immediately hand each flushed sentence string to Kokoro's
   `generate_stream()`.

## What to measure

1. **Time-to-first-audio** — from "participant utterance ends" to "first
   audio sample plays." Compare against today's full-batch baseline
   (wait for complete LLM response, then run the whole thing through TTS).
2. **Inter-sentence gaps** — does sentence 2's audio begin immediately
   after sentence 1 finishes playing, or is there an audible stall because
   the LLM hasn't generated it yet?
3. **Buffer correctness** — run all three `CONVERSATION*` scripts through
   the harness and check for: flushing mid-abbreviation (e.g. "Mr.",
   "..."), dropped trailing fragments when the LLM stream ends, or
   double-flushing the same sentence.

## Pass / fail

Pass if: time-to-first-audio lands meaningfully under the current
full-pipeline baseline (target: the 1-2s window cited in the latency
research doc), and the buffer logic doesn't glitch on any of the three
conversation scripts. If it passes, the same buffer implementation carries
over unchanged to whichever TTS engine wins
`2026-07-23-tts-streaming-check.md` — this experiment is only proving the
buffer, not picking a shipping engine.
