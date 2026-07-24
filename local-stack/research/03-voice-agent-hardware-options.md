# Research snapshot — hardware options for a local voice-agent pipeline (2026-07-23)

Point-in-time background research, not a living decision log (contrast with
`tts/DECISION.md`, `stt/DECISION.md`, `llm/DECISION.md`). Follows directly
from `02-local-voice-agent-latency.md` — that file's ChipChat
reference (Mac Studio, M2 Ultra, 192GB unified memory) prompted the question
of what hardware mirror.me-radio would actually need to run a similar local
ASR→LLM→TTS pipeline.

## Key takeaways

- **ChipChat's 192GB was for model quality (a 45B-param MoE), not latency.**
  - The 192GB ran a large Mixtral-8x7B-based mixture-of-experts model (8
    experts, 45B total params) for better general conversation quality.
  - mirror.me-radio's fixed narrator character giving short,
    scripted-adjacent responses doesn't need a model that big, or that
    memory footprint.
- **16GB (current M5 Air) already clears the floor** for a 7-8B 4-bit model
  — the realistic model size for this use case (per
  `02-local-voice-agent-latency.md`'s recommended stack).
- **24-32GB is the comfortable target.**
  - Headroom so LLM + streaming Whisper + TTS can all be resident
    simultaneously, without the kind of memory pressure that drove the
    Parler timing regressions documented in `tts/DECISION.md` ("Parler
    stage-1 timing re-run, quiet machine").
  - Also leaves room to try a larger/better-quality model than 7-8B if that
    class feels too flat for a narrator voice.
- **Concrete recommendation: Mac mini (M4 Pro, 24GB).**
  - Cheapest option that clears the bar.
  - Small, close-to-silent — good physical fit for hardware that needs to
    disappear into an installation.
  - A Mac Studio or the Ultra tier is not needed — that tier is built for
    the 45B-parameter-class models ChipChat used, not this project's scope.
- Apple's rumored M5 Max/Ultra Mac Studio refresh is **not relevant to this
  project** — noted only because it came up in the same conversation.
  - Reportedly delayed to around October 2026, due to memory-chip supply
    issues.[^1]
  - Base memory reportedly rising: M5 Max starting at 36GB, M5 Ultra
    starting at 96GB. Apple tested support for up to 768GB but supply
    constraints may prevent that configuration from actually shipping.
  - Pricing uncertain, trending upward — when Apple last raised Mac Studio
    prices, the 96GB configuration went from $3,999 to $5,299; speculation
    that an 8x-RAM top config could exceed $10,000.[^2]
- **No true out-of-the-box appliance exists** for "local ASR→LLM→TTS agent,
  custom voice, sub-2s turn-taking." Closest options (Home Assistant Voice
  PE, Jetson dev kits, Strix Halo mini PCs, Pipecat/LiveKit) all still
  require assembling the pipeline yourself.

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

## The Mac mini is the path of least resistance, not a compromise

Given this project is already deep in the Apple/MLX ecosystem (existing
`local-stack/tts/` scripts, `.venv-*` per-model environments, MLX-native
tooling), the path of least resistance is a Mac mini with more memory than
the current M5 Air — same tools, same code, just headroom — rather than
switching platforms or waiting for an out-of-the-box appliance that doesn't
exist yet.

## Sources

[^1]: MacRumors, M5 Ultra Mac Studio 2026 delay — https://www.macrumors.com/2026/06/25/m5-ultra-mac-studio-2026/
[^2]: Macworld, 2026 Mac Studio M5 pricing rumors — https://www.macworld.com/article/2973459/2026-mac-studio-m5-release-date-specs-price-rumors.html
