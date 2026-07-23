# Research snapshot — hardware options for a local voice-agent pipeline (2026-07-23)

Point-in-time background research, not a living decision log (contrast with
`tts/DECISION.md`, `stt/DECISION.md`, `llm/DECISION.md`). Follows directly
from `2026-07-23-local-voice-agent-latency.md` — that file's ChipChat
reference (Mac Studio, M2 Ultra, 192GB unified memory) prompted the question
of what hardware mirror.me-radio would actually need to run a similar local
ASR→LLM→TTS pipeline.

## Key takeaways

- **ChipChat's 192GB was for model quality (a 45B-param MoE), not latency.**
  mirror.me-radio's fixed narrator character doesn't need a model that big.
- **16GB (current M5 Air) already clears the floor** for a 7-8B 4-bit model.
  **24-32GB is the comfortable target** — headroom so LLM + Whisper + TTS
  can all be resident without the memory pressure that caused the Parler
  timing regressions in `tts/DECISION.md`.
- **Concrete recommendation: Mac mini (M4 Pro, 24GB).** Cheapest option that
  clears the bar, small/quiet, good fit for an installation. A Mac Studio or
  the Ultra tier is not needed.
- Apple's rumored M5 Max/Ultra Mac Studio refresh (~Oct 2026, pricing/RAM
  still uncertain) is **not relevant to this project** — noted only because
  it came up in the same conversation.
- **No true out-of-the-box appliance exists** for this ("local ASR→LLM→TTS
  agent, custom voice, sub-2s turn-taking"). Closest options (Home Assistant
  Voice PE, Jetson dev kits, Strix Halo mini PCs, Pipecat/LiveKit) all still
  require assembling the pipeline yourself. Given this project is already
  in the Apple/MLX ecosystem, a Mac mini with more memory than the M5 Air is
  the path of least resistance.

## Correcting the 192GB takeaway

ChipChat's 192GB wasn't a **latency** requirement — it was there so the
project could run a large model (a Mixtral-8x7B-based mixture-of-experts
model, 8 experts, 45B total parameters) for better general conversation
quality. mirror.me-radio doesn't need that: a fixed narrator character giving
short, scripted-adjacent responses is well served by a much smaller model, and
a much smaller memory footprint.

## What machine this project actually needs

- **16GB (current MacBook Air M5) is workable for prototyping** — explicitly
  the floor for running a 7-8B parameter model at 4-bit quantization, the
  realistic model size for this use case (per
  `2026-07-23-local-voice-agent-latency.md`'s recommended stack).
- **24-32GB unified memory is the comfortable target** — headroom for the
  LLM, streaming Whisper, and TTS to all be resident simultaneously without
  the kind of memory pressure that drove the Parler timing regressions
  documented in `tts/DECISION.md` ("Parler stage-1 timing re-run, quiet
  machine"). Also leaves room to try a larger/better-quality model than 7-8B
  if that class feels too flat for a narrator voice.
- **Concrete cheapest option that clears the bar: Mac mini (M4 Pro, 24GB).**
  Small, close-to-silent, a good physical fit for hardware that needs to
  disappear into an installation.
- **A Mac Studio (or the Ultra tier at all) is not needed.** That tier is
  built for the 45B-parameter-class models ChipChat used, not this project's
  scope.

## Apple's upcoming Mac Studio refresh (context only, not a recommendation)

Rumored M5 Max/Ultra Mac Studio refresh, not yet released as of this
research date:
- Timeline: reportedly delayed from an earlier-2026 target to around October
  2026, due to memory-chip supply issues.
  Source: [MacRumors](https://www.macrumors.com/2026/06/25/m5-ultra-mac-studio-2026/)
- Base memory reportedly rising: M5 Max starting at 36GB, M5 Ultra starting
  at 96GB. Apple tested support for up to 768GB but supply constraints may
  prevent that configuration from actually shipping.
- Pricing uncertain and trending upward — when Apple last raised Mac Studio
  prices, the 96GB configuration went from $3,999 to $5,299; speculation
  that an 8x-RAM top config could exceed $10,000.
  Source: [Macworld](https://www.macworld.com/article/2973459/2026-mac-studio-m5-release-date-specs-price-rumors.html)
- None of this is relevant to mirror.me-radio's actual requirement — recorded
  here only because it came up in the same research conversation and could
  otherwise be mistakenly read as "what we need."

## Is there anything out-of-the-box?

No true out-of-the-box **appliance** exists for "local ASR→LLM→TTS
conversational agent with a custom character voice, sub-2s turn-taking."
What exists, and why each falls short of "just buy this":

- **Home Assistant Voice PE** — open-source, local-first voice hardware; the
  closest thing to a genuine appliance (a physical mic/speaker puck), but
  it's a satellite device that talks to a separate local server running the
  actual models, and it's built for smart-home intent-matching, not open
  narrator conversation. Still need a Mac/PC behind it doing the real work.
- **NVIDIA Jetson Orin Nano Super / AGX Orin dev kits** — purpose-built
  small-form-factor AI boards used in local voice-agent projects, but
  they're dev kits (install and wire everything yourself), and the ARM+CUDA
  toolchain is a different stack than the MLX/whisper.cpp work already done
  in this repo.
- **AMD Strix Halo mini PCs** (Framework Desktop, GMKtec EVO-X2, etc.) — x86
  boxes with up to 128GB unified GPU-addressable memory at consumer prices,
  currently popular for local-LLM hosting. Same caveat: a mini PC you build
  the pipeline onto, not an appliance.
- **Ollama / LM Studio** — make the local-LLM piece easy, but are not
  voice-agent products; you'd still wire VAD → ASR → LLM → TTS yourself.
- **Pipecat / LiveKit Agents** — the closest to "out of the box" for the
  *orchestration* layer (streaming, sentence-chunking, interruption
  handling are provided), but you still plug in your own local ASR/LLM/TTS
  models and write the glue code.

**Conclusion:** given this project is already deep in the Apple/MLX
ecosystem (existing `local-stack/tts/` scripts, `.venv-*` per-model
environments, MLX-native tooling), the path of least resistance is a Mac
mini with more memory than the current M5 Air — same tools, same code, just
headroom — rather than switching platforms or waiting for an out-of-the-box
appliance that doesn't exist yet.
