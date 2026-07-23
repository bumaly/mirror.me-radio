# Research snapshot — local voice-agent latency (ASR→LLM→TTS) (2026-07-23)

Point-in-time background research, not a living decision log (contrast with
`tts/DECISION.md`, `stt/DECISION.md`, `llm/DECISION.md`). This is the research
that actually applies to mirror.me-radio, once the investigation narrowed from
"replicate Google Meet's translation architecture" (see
`2026-07-23-google-speech-translation-architecture.md`) to the project's real
requirement: a **fully local, air-gapped, no-cloud-APIs, no-voice-cloning-
needed** conversational pipeline that minimizes the gap between the person
finishing speaking and the installation's spoken response starting — target
**~1-2 seconds** end-to-end, prototyping on a MacBook Air M5, 16GB unified
memory (Apple Silicon/MPS), with a more capable dedicated machine planned but
not yet chosen.

**Provenance note:** this research came from an automated multi-agent
research workflow. Its final synthesis step glitched on this run and returned
placeholder text instead of a real write-up. The content below was
reconstructed by hand directly from the run's verified claims and raw source
evidence (not from the broken auto-summary), so individual figures are
flagged by how well-corroborated they are — treat single-source ballparks as
just that, ballparks, not benchmarked facts.

## Key takeaways

- No local unified speech-to-speech model is fast enough yet (best option,
  Qwen2.5-Omni-7B, runs at ~0.5x realtime). The realistic architecture is a
  **cascaded ASR→LLM→TTS pipeline with genuine overlap between stages** —
  same pattern production frameworks like Pipecat/LiveKit Agents use.
- **Overlap matters more than any single stage's raw speed**: a blocking
  pipeline sums stage latencies (~1.5-2s+); a streaming/overlapped one
  collapses toward the slowest single stage. Mechanism: buffer LLM tokens to
  a sentence boundary (`.!?`), forward each sentence to TTS immediately,
  keep generating the rest.
- **ChipChat** is the one real local proof-of-concept found: ~920ms
  end-to-end, fully on-device on a Mac Studio M2 Ultra 192GB. Its 192GB was
  for a large 45B-param model for *quality*, not required for the latency —
  see `2026-07-23-voice-agent-hardware-options.md`.
- Rough per-stage budget: **VAD/endpointing ~150-800ms**, **ASR
  ~100-400ms**, **LLM time-to-first-token ~150-400ms** (small 4-bit
  quantized model + prompt caching), **TTS time-to-first-audio ~90-300ms**
  (Kokoro-82M streaming — see TTS reconciliation note below). Landing in the 1-2s target is realistic but
  requires deliberately choosing the fast/small option at every stage, not
  defaults.
- **Recommended stack to prototype:** Silero VAD → whisper.cpp/MLX-Whisper
  (small/turbo, streaming) → 7-8B 4-bit LLM via `mlx-lm` (prompt caching,
  capped KV-cache) → hand-rolled sentence-boundary buffer → Kokoro-82M via
  `kokoro-mlx`/`mlx-audio` streaming synthesis.
- Nothing here has been run on the actual M5 Air yet — this is a planning
  budget from external sources, not measured results.

**Reconciliation with `llm/DECISION.md` (added after cross-check):** this
research's "7-8B model" recommendation was written green-field, from generic
latency/quality sourcing, without checking what the project had already
decided. `llm/DECISION.md` screened 8 candidates over 5 rounds specifically
for **holding a fictional child-character persona** (strict vocabulary,
format, and disclosure-pacing rules) — not generic chat quality — and every
7B+ model tested (dolphin-mistral, nous-hermes2, mistral, gemma2:2b,
phi3:mini) was disqualified, either on latency (15-75s/turn) or on
character/format discipline (adult-register drift, metaphors, stage-direction
leakage). **llama3.2:3b won** and is the final decision, consistently
sub-3s/turn in isolation. For this project, treat "7-8B" below as generic
background, not a recommendation to act on — the smaller model already in
place satisfies both the latency budget and a persona-fidelity requirement
this research didn't account for.

## The realistic target isn't a single unified model

Fully self-hosted, end-to-end (native) speech-to-speech models aren't yet
viable for local realtime use. The best local option found
(Qwen2.5-Omni-7B, DiT-based Talker) runs at roughly 0.5x realtime — meaning
~13 seconds of compute for ~6.5 seconds of audio. So the realistic
architecture is a **cascaded ASR→LLM→TTS pipeline where the stages overlap in
time**, not a single unified model and not a naive blocking cascade either.
This is also exactly the pattern production voice-agent frameworks (Pipecat,
LiveKit Agents) are built around.

## Why overlap matters more than any single stage's raw speed

A naive/blocking pipeline sums stage latencies: VAD + ASR + LLM + TTS ≈
1.5-2s+. With genuine overlap between stages, total latency collapses toward
roughly the **slowest single stage** instead of the **sum of all stages** —
this is the one point every source in this research converged on with zero
contradiction. The concrete mechanism, described identically by multiple
independent sources:

- Pipecat's `TTSService` exposes a `TextAggregationMode` with a `SENTENCE`
  mode (buffer LLM tokens until sentence-ending punctuation, then forward to
  TTS) and a `TOKEN` mode (stream tokens directly, lower latency, less
  natural prosody). This is a first-class, documented configuration option,
  not an ad hoc trick.
  Source: [Pipecat TTS service reference](https://reference-server.pipecat.ai/en/stable/api/pipecat.services.tts_service.html)
- The same "sentence aggregation" pattern is independently confirmed in
  LiveKit's own docs (a sentence tokenizer splits streamed LLM text before
  synthesis when the TTS backend lacks native streaming).
- An arXiv voice-agent tutorial gives explicit formulas for the same idea:
  sequential/turn-based latency `T_STT + T_LLM + T_TTS ≈ 400 + 800 + 400 =
  1600ms`, vs. streaming/overlapped `T_STT + T_LLM-first-sentence +
  T_TTS-TTFB ≈ 400 + 300 + 200 = 900ms`, with an actual measured 755ms in
  their cascaded pipeline (note: their pipeline used cloud Deepgram STT +
  ElevenLabs TTS, not a local stack — cited here only to support the general
  "overlap halves latency" principle, not as a local-hardware number).
  Source: [arXiv:2603.05413](https://arxiv.org/pdf/2603.05413) ("Building
  Enterprise Realtime Voice Agents from Scratch")

**Practical takeaway:** buffer LLM output until you hit `.`/`!`/`?`, hand
that fragment to TTS immediately, keep generating the rest — TTS starts
producing audio while the LLM is still mid-response.

## ChipChat — the one real local proof-of-concept found

A cascaded ASR→LLM→TTS voice agent running **fully on-device on Apple
Silicon** (Mac Studio, M2 Ultra, **192GB**), achieving sub-second (~920ms)
total response latency by streaming partial outputs between every stage:
ASR tokens streamed to the LLM as generated, LLM tokens streamed to TTS as
generated. Its detailed latency table attributes most of the ~920ms to the
LLM's "pause before first output" stage (~560ms of the total), with ASR
contributing ~165-175ms.

**Important correction for hardware planning:** the 192GB in this system was
there to run a large model for **conversation quality** (a Mixtral-8x7B-based
mixture-of-experts model, 8 experts, 45B total parameters) — not because
192GB is required to hit this latency. A fixed narrator character giving
short, scripted-adjacent responses doesn't need a model anywhere near that
size. See `2026-07-23-voice-agent-hardware-options.md` for the actual memory
requirement.

Without ChipChat's streaming/caching optimizations, a naive PyTorch cascaded
implementation (with only the LLM in MLX) exceeded 4 seconds total — a
reminder that the engineering (streaming between stages, caching) matters as
much as model choice.

## Per-stage latency budget

Ranges below mix well-corroborated figures with single-source ballparks —
noted per line. None of these were independently re-benchmarked on this
project's actual hardware; they're a planning budget, not measured results.

**VAD / endpointing: ~150-800ms** — this is the dial actually under your
control, and the most load-bearing one for feel.
- Silero VAD itself is near-instant: ~1ms per 32ms audio chunk on CPU.
- The real latency is the **silence threshold** chosen before declaring
  "they're done": ~200-300ms feels snappy but risks cutting someone off
  mid-sentence; ~600-900ms is safer but slower. This exact tradeoff is
  documented directly in LiveKit's turn-detection docs.
  Source: [docs.livekit.io/agents/logic/turns](https://docs.livekit.io/agents/logic/turns/)
- Silero VAD substantially outperforms WebRTC VAD on endpointing accuracy (at
  a 5% false-positive rate, Silero hits ~87.7% true-positive vs. roughly 50%
  for WebRTC).
- LiveKit's "Turn Detector Model" layers semantic content on top of raw VAD
  to catch true end-of-turn without just waiting out a fixed silence window —
  useful if a plain VAD threshold cuts off young/hesitant speakers
  mid-sentence in this installation's actual use.
- One paper (Mimi neural-audio-codec endpointer, label-delay trained) claims
  a 160ms median endpoint latency with a 7.01% cutoff error rate — a
  research-grade result, not something to expect out of the box.
  Source: [arXiv:2506.07081](https://arxiv.org/pdf/2506.07081)

**ASR finalization: ~100-400ms** (single-source ballparks, not independently
verified — treat as directional):
- whisper.cpp — dependency-free C/C++ Whisper port, Metal-accelerated on
  Apple Silicon, ships a built-in `stream` example for live microphone
  transcription, supports quantization (e.g. `q5_0` shrinks large-v3 from
  ~3GB to ~1.1GB with negligible accuracy loss).
- MLX-Whisper — reported (one source, not independently corroborated) as
  30-40% faster than whisper.cpp on Apple Silicon.
- `whisper_streaming` (ufal) — uses a **LocalAgreement-n** policy: a
  transcript prefix is only confirmed once n consecutive incremental updates
  agree on it (default n=2), trading a little latency for stability against
  the transcript flip-flopping. Supports an MLX backend. Marked outdated as
  of 2025, superseded by "SimulStreaming."
  Source: [github.com/ufal/whisper_streaming](https://github.com/ufal/whisper_streaming)

**LLM time-to-first-token: ~150-400ms** achievable with a small (7-8B),
4-bit-quantized model served via MLX, given:
- Prompt caching and using a smaller model are the biggest software levers
  for cutting time-to-first-token (prompt caching alone can drop TTFT by
  200-400ms per one source).
- Capping KV-cache size (e.g. to 4096 tokens) avoids memory pressure that can
  degrade throughput by up to 10x — directly relevant to sustaining low TTFT
  across a multi-turn conversation on a 16GB machine.
- Naive/uncached setups can balloon badly as conversation history grows: one
  source cites LLM TTFT shifting from 566ms at p50 to 2,246ms at p95 purely
  from context growth.
- Speculative decoding can boost throughput ~1.6x (from ~38 to ~62 tok/s on
  Apple Silicon) when a draft model's acceptance rate exceeds 0.65 — a later
  optimization, not a starting-point requirement.

**TTS time-to-first-audio: ~90-300ms** with a genuinely streaming engine:
- Kokoro-82M via `kokoro-mlx`/`mlx-audio` — **confirmed by reading the actual
  source code**, not just marketing copy: `generate_stream()` splits text
  into phoneme chunks and yields audio incrementally per chunk inside the
  generation loop (true streaming, not "generate everything then slice"),
  and playback uses a persistent `sounddevice.OutputStream` so generation and
  playback overlap with no inter-chunk silence. This is the same model
  family (Kokoro/MeloTTS) already used in this repo's OpenVoice split
  pipeline — real synergy with existing `local-stack/tts/` work.
- One blog's ballpark numbers (not independently verified): Piper ~40ms
  time-to-first-audio on an M5 Max, Kokoro ~90ms, XTTS v2 ~600ms (XTTS's
  latency profile is called out as impractical for live conversational use
  even though it supports voice cloning — consistent with this project's
  independent finding that OpenVoice/XTTS cloning fidelity and latency don't
  come for free).
  **See TTS reconciliation note below — Kokoro is not a candidate for this
  project's actual TTS choice.**

## Recommended concrete stack to prototype

- **VAD:** Silero VAD, tuned silence threshold (start ~500ms, adjust by ear
  for how a child speaks/pauses in this installation's actual use case).
- **ASR:** whisper.cpp or MLX-Whisper, small/turbo quantized model, streaming
  mode.
- **LLM:** a 7-8B model, 4-bit quantized, served via `mlx-lm`, prompt caching
  on, KV-cache capped.
- **Aggregator:** a hand-rolled sentence-boundary buffer (Pipecat's pattern —
  trivial to replicate: accumulate tokens, flush on `.!?`).
- **TTS:** Kokoro-82M via `kokoro-mlx` or `mlx-audio`'s `generate_stream()`.

**Reconciliation with `tts/DECISION.md` (added after cross-check):** this
research's Kokoro recommendation was written green-field, from generic
TTS-latency sourcing, without checking what the project had already decided.
`tts/DECISION.md` screened TTS candidates specifically for **cloning the
narrator's own voice** from a reference recording (`narrator_ref.wav`) —
voice identity is a first-class pass/fail column there, not a nice-to-have.
Kokoro (and Piper) were explicitly **rejected**: "✗ no character... built-in
voices only, no cloning." Both were removed from the codebase the same day
(commit `7e0be43`) — the `mlx_audio_tts.py`/`piper_tts.py` adapters and
Kokoro's synth clips are gone. This isn't a wholesale rejection of "fast
local TTS" as a category, only of Kokoro specifically for this project's
cloning requirement.

The real standing candidates per `tts/DECISION.md` are **OpenVoice V2**
(0.31x RTF) and **XTTS-v2** (0.76x RTF) — both clone the narrator's voice
from `narrator_ref.wav`, both still well under real-time, but neither is
anywhere near Kokoro's ~90ms time-to-first-audio. If streaming/low-latency
TTS synthesis matters for the live-conversation use case (per `README.md`,
this is a real-time STT→LLM→TTS pipeline per Storypoint interaction, not
pre-recorded narration), that gap is a real tradeoff against voice fidelity
worth flagging, not something to paper over. For this project, treat the
Kokoro figures above as generic TTS-latency background, not a recommendation
to act on — swap the "TTS:" line above for OpenVoice V2 or XTTS-v2 depending
on whether latency or cloning accuracy is prioritized.

Stacked with genuine overlap between stages, landing in the 1-2s
response-gap range is realistic but not automatic — it requires deliberately
picking the fast/small option at each stage (small quantized LLM, prompt
caching, a tuned-not-too-conservative VAD threshold, a genuinely streaming
TTS) rather than defaults.

## Next steps (not yet done)

- No component of this stack has been run/benchmarked on the actual M5 Air
  yet — this is a planning budget from external sources, not measured
  results on this project's hardware.
- StreamSpeech's chunk/alignment-policy idea (see the companion translation
  research file) could inform a smarter endpointing policy later, but isn't
  needed to get a first working prototype.
