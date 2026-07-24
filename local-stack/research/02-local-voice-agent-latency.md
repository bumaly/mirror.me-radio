# Research snapshot — local voice-agent latency (ASR→LLM→TTS) (2026-07-23)

Point-in-time background research, not a living decision log (contrast with
`tts/DECISION.md`, `stt/DECISION.md`, `llm/DECISION.md`).

- Started from curiosity: encountered Google Meet's live translation feature,
  investigated its architecture to see what transfers
  (`01-google-speech-translation-architecture.md`). Conclusion: doesn't
  transfer, but pointed at the project's real requirement instead.
- Requirement: fully local, air-gapped, no-cloud-APIs, no-voice-cloning
  pipeline.
- Target: minimize gap between person finishing speaking and the
  installation's spoken response starting. ~1-2s end-to-end.
- Hardware: prototyping on MacBook Air M5, 16GB unified memory (Apple
  Silicon/MPS). Dedicated machine planned, not chosen yet.

**Provenance:**
- Came from an automated multi-agent research workflow.
- Final synthesis step glitched this run, returned placeholder text instead
  of a real write-up.
- Content below reconstructed by hand from the run's verified claims + raw
  source evidence, not the broken auto-summary.
- Figures flagged by corroboration strength below. Treat single-source
  ballparks as ballparks, not benchmarked facts.

## Key takeaways

- No local unified speech-to-speech model fast enough yet. Best option:
  Qwen2.5-Omni-7B, ~0.5x realtime. Realistic architecture: cascaded
  ASR→LLM→TTS with genuine overlap between stages. Same pattern production
  frameworks (Pipecat/LiveKit Agents) use.
- Overlap matters more than any single stage's raw speed. Blocking pipeline
  sums latencies (~1.5-2s+). Streaming/overlapped pipeline collapses toward
  the slowest single stage. Mechanism: buffer LLM tokens to a sentence
  boundary (`.!?`), forward each sentence to TTS immediately, keep
  generating the rest.
- ChipChat: one real local proof-of-concept found. ~920ms end-to-end, fully
  on-device, Mac Studio M2 Ultra 192GB. 192GB was for a large 45B-param
  model for quality, not required for the latency. See
  `03-voice-agent-hardware-options.md`.
- Rough per-stage budget: VAD/endpointing ~150-800ms. ASR ~100-400ms. LLM
  time-to-first-token ~150-400ms (small 4-bit quantized model + prompt
  caching). TTS time-to-first-audio ~90-300ms (Kokoro-82M streaming, see TTS
  reconciliation note below). Landing in the 1-2s target is realistic but
  requires deliberately choosing the fast/small option at every stage, not
  defaults.
- Recommended stack to prototype: Silero VAD → whisper.cpp/MLX-Whisper
  (small/turbo, streaming) → 7-8B 4-bit LLM via `mlx-lm` (prompt caching,
  capped KV-cache) → hand-rolled sentence-boundary buffer → Kokoro-82M via
  `kokoro-mlx`/`mlx-audio` streaming synthesis.
- Nothing here has been run on the actual M5 Air yet. Planning budget from
  external sources, not measured results.

**Reconciliation with `llm/DECISION.md`:**
- This research's "7-8B model" recommendation was written green-field, from
  generic latency/quality sourcing, without checking the existing project
  decision.
- `llm/DECISION.md` screened 8 candidates over 5 rounds for holding a
  fictional child-character persona (strict vocabulary, format,
  disclosure-pacing rules), not generic chat quality.
- Every 7B+ model tested (dolphin-mistral, nous-hermes2, mistral, gemma2:2b,
  phi3:mini) disqualified — either on latency (15-75s/turn) or on
  character/format discipline (adult-register drift, metaphors,
  stage-direction leakage).
- llama3.2:3b won. Final decision. Consistently sub-3s/turn in isolation.

Treat "7-8B" below as generic background, not a recommendation to act on.
The smaller model already in place satisfies both the latency budget and a
persona-fidelity requirement this research didn't account for.

## The realistic target isn't a single unified model

- Fully self-hosted, end-to-end (native) speech-to-speech models aren't
  viable yet for local realtime use.
- Best local option found: Qwen2.5-Omni-7B (DiT-based Talker). Runs at
  roughly 0.5x realtime — ~13s of compute for ~6.5s of audio.
- Production voice-agent frameworks (Pipecat, LiveKit Agents) are built
  around the same cascaded+overlapped pattern.

Realistic architecture: a cascaded ASR→LLM→TTS pipeline where the stages
overlap in time. Not a single unified model, not a naive blocking cascade
either.

## Overlap collapses total latency toward the slowest stage, not the sum

- Blocking pipeline: VAD+ASR+LLM+TTS latencies add up, ≈1.5-2s+.
- Overlapped: total ≈ slowest single stage.
- Every source agrees, no exceptions found.
- Mechanism: buffer LLM tokens to a sentence boundary (`.!?`), send each
  sentence to TTS as soon as it closes, keep generating the rest.
- Confirmed in both major frameworks:
  - Pipecat `TTSService`: `SENTENCE` mode does exactly this.[^1]
    - vs. `TOKEN` mode: streams raw tokens, lower latency, worse prosody.
  - LiveKit: same pattern, own sentence tokenizer.[^2]
    - Used when the TTS backend lacks native streaming.
  - arXiv formula:[^3]
    - Sequential: `T_STT+T_LLM+T_TTS ≈ 400+800+400 = 1600ms`.
    - Overlapped: `≈ 400+300+200 = 900ms`.
    - Measured 755ms in their (cloud) pipeline.
- First-class feature in both major frameworks. Not a workaround. Safe to
  build on rather than treat as a hack.

## ChipChat — the one real local proof-of-concept found

- Cascaded ASR→LLM→TTS voice agent, fully on-device, Apple Silicon (Mac
  Studio, M2 Ultra, 192GB).
- ~920ms total response latency. Achieved by streaming partial outputs
  between every stage: ASR tokens → LLM as generated, LLM tokens → TTS as
  generated.
- Latency table: ~560ms of the 920ms is the LLM's "pause before first
  output" stage. ASR contributes ~165-175ms.
- 192GB was for conversation quality (Mixtral-8x7B-based MoE, 8 experts,
  45B total params), not required for this latency. See
  `03-voice-agent-hardware-options.md` for the actual memory requirement.
- Without ChipChat's streaming/caching optimizations: a naive PyTorch
  cascaded implementation (LLM-only in MLX) exceeded 4s total.

Engineering (streaming between stages, caching) matters as much as model
choice here — a fixed narrator character giving short, scripted-adjacent
responses doesn't need anywhere near 192GB.

## Per-stage latency budget

Ranges mix well-corroborated figures with single-source ballparks, noted per
line. None independently re-benchmarked on this project's actual hardware —
a planning budget, not measured results.

**VAD / endpointing: ~150-800ms** — the dial actually under your control,
most load-bearing for feel.
- Silero VAD itself near-instant: ~1ms per 32ms audio chunk on CPU.
- Real latency is the silence threshold chosen before declaring "they're
  done": ~200-300ms feels snappy but risks cutting someone off mid-sentence.
  ~600-900ms safer but slower. Documented directly in LiveKit's
  turn-detection docs.[^2]
- Silero VAD substantially outperforms WebRTC VAD on endpointing accuracy:
  at a 5% false-positive rate, Silero ~87.7% true-positive vs. ~50% for
  WebRTC.
- LiveKit's "Turn Detector Model" layers semantic content on top of raw VAD
  to catch true end-of-turn without waiting out a fixed silence window.
  Useful if a plain VAD threshold cuts off young/hesitant speakers
  mid-sentence in this installation's actual use.
- Mimi neural-audio-codec endpointer (label-delay trained): 160ms median
  endpoint latency, 7.01% cutoff error rate.[^4] Research-grade result, not
  out-of-the-box.

**ASR finalization: ~100-400ms** (single-source ballparks, not
independently verified, treat as directional):
- whisper.cpp: dependency-free C/C++ Whisper port, Metal-accelerated on
  Apple Silicon, ships a built-in `stream` example for live mic
  transcription, supports quantization (e.g. `q5_0` shrinks large-v3 from
  ~3GB to ~1.1GB, negligible accuracy loss).
- MLX-Whisper: reported (one source, not corroborated) 30-40% faster than
  whisper.cpp on Apple Silicon.
- `whisper_streaming` (ufal): LocalAgreement-n policy — transcript prefix
  confirmed only once n consecutive incremental updates agree (default
  n=2). Trades a little latency for stability against transcript
  flip-flopping. Supports an MLX backend. Marked outdated as of 2025,
  superseded by "SimulStreaming."[^5]

**LLM time-to-first-token: ~150-400ms** achievable with a small (7-8B),
4-bit-quantized model served via MLX, given:
- Prompt caching + smaller model = biggest software levers for cutting
  TTFT. Prompt caching alone can drop TTFT by 200-400ms (one source).
- Capping KV-cache size (e.g. 4096 tokens) avoids memory pressure that can
  degrade throughput up to 10x. Directly relevant to sustaining low TTFT
  across a multi-turn conversation on a 16GB machine.
- Naive/uncached setups balloon badly as conversation history grows: one
  source cites LLM TTFT shifting from 566ms p50 to 2,246ms p95 purely from
  context growth.
- Speculative decoding: ~1.6x throughput boost (~38→~62 tok/s on Apple
  Silicon) when a draft model's acceptance rate exceeds 0.65. Later
  optimization, not a starting-point requirement.

**TTS time-to-first-audio: ~90-300ms** with a genuinely streaming engine:
- Kokoro-82M via `kokoro-mlx`/`mlx-audio`: confirmed by reading the actual
  source code, not marketing copy. `generate_stream()` splits text into
  phoneme chunks, yields audio incrementally per chunk inside the
  generation loop (true streaming, not generate-then-slice). Playback uses
  a persistent `sounddevice.OutputStream`, generation and playback overlap
  with no inter-chunk silence. Same model family (Kokoro/MeloTTS) already
  used in this repo's OpenVoice split pipeline — real synergy with existing
  `local-stack/tts/` work.
- One blog's ballpark numbers (not independently verified): Piper ~40ms
  TTFA on M5 Max, Kokoro ~90ms, XTTS v2 ~600ms. XTTS's latency profile
  called out as impractical for live conversational use even though it
  supports voice cloning — consistent with this project's independent
  finding that OpenVoice/XTTS cloning fidelity and latency don't come free.

See TTS reconciliation note below: Kokoro is not a candidate for this
project's actual TTS choice.

## Recommended concrete stack to prototype

- VAD: Silero VAD, tuned silence threshold (start ~500ms, adjust by ear for
  how a child speaks/pauses in this installation's actual use case).
- ASR: whisper.cpp or MLX-Whisper, small/turbo quantized model, streaming
  mode.
- LLM: 7-8B model, 4-bit quantized, served via `mlx-lm`, prompt caching on,
  KV-cache capped.
- Aggregator: hand-rolled sentence-boundary buffer (Pipecat's pattern,
  trivial to replicate: accumulate tokens, flush on `.!?`).
- TTS: Kokoro-82M via `kokoro-mlx` or `mlx-audio`'s `generate_stream()`.

**Reconciliation with `tts/DECISION.md`:**
- This research's Kokoro recommendation was written green-field, from
  generic TTS-latency sourcing, without checking the existing project
  decision.
- `tts/DECISION.md` screened TTS candidates for cloning the narrator's own
  voice from a reference recording (`narrator_ref.wav`). Voice identity is
  a first-class pass/fail column there, not a nice-to-have.
- Kokoro (and Piper) explicitly rejected: "✗ no character... built-in
  voices only, no cloning." Both removed from the codebase the same day
  (commit `7e0be43`) — `mlx_audio_tts.py`/`piper_tts.py` adapters and
  Kokoro's synth clips gone.
- Not a wholesale rejection of "fast local TTS" as a category. Only Kokoro
  specifically, for this project's cloning requirement.
- Real standing candidates per `tts/DECISION.md`: OpenVoice V2 (0.31x RTF)
  and XTTS-v2 (0.76x RTF). Both clone the narrator's voice from
  `narrator_ref.wav`, both well under real-time, neither anywhere near
  Kokoro's ~90ms TTFA.

If streaming/low-latency TTS synthesis matters for the live-conversation
use case (per `README.md`, this is a real-time STT→LLM→TTS pipeline per
Storypoint interaction, not pre-recorded narration), that gap is a real
tradeoff against voice fidelity worth flagging, not something to paper
over. Treat the Kokoro figures above as generic TTS-latency background, not
a recommendation to act on — swap the "TTS:" line above for OpenVoice V2 or
XTTS-v2 depending on whether latency or cloning accuracy is prioritized.

Stacked with genuine overlap between stages, landing in the 1-2s
response-gap range is realistic but not automatic. Requires deliberately
picking the fast/small option at each stage (small quantized LLM, prompt
caching, a tuned-not-too-conservative VAD threshold, a genuinely streaming
TTS) rather than defaults.

## Next steps (not yet done)

- No component of this stack has been run/benchmarked on the actual M5 Air
  yet. Planning budget from external sources, not measured results on this
  project's hardware.
- StreamSpeech's chunk/alignment-policy idea (see the companion translation
  research file) could inform a smarter endpointing policy later. Not
  needed to get a first working prototype.

## Sources

[^1]: Pipecat TTS service reference — https://reference-server.pipecat.ai/en/stable/api/pipecat.services.tts_service.html
[^2]: LiveKit turn-detection docs — https://docs.livekit.io/agents/logic/turns/
[^3]: arXiv:2603.05413 ("Building Enterprise Realtime Voice Agents from Scratch") — https://arxiv.org/pdf/2603.05413
[^4]: arXiv:2506.07081 (Mimi neural-audio-codec endpointer) — https://arxiv.org/pdf/2506.07081
[^5]: whisper_streaming (ufal) — https://github.com/ufal/whisper_streaming
