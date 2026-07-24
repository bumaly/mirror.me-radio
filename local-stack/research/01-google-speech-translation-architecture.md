# Research snapshot — real-time speech-to-speech translation architecture (2026-07-23)

Point-in-time background research, not a living decision log (contrast with
`tts/DECISION.md`, `stt/DECISION.md`, `llm/DECISION.md`). Triggered by
experiencing Google Meet's live speech translation feature and asking whether
its architecture could inform this project. Conclusion up front: **this
specific architecture (translation with voice cloning) is not what
mirror.me-radio needs** — see `02-local-voice-agent-latency.md` for the
pipeline that actually applies here. This file exists so the research isn't
lost.

## Key takeaways

- Google Meet's live translation is a **single end-to-end model** — streaming
  encoder + streaming decoder, transformer + AudioLM based, no text
  intermediate — not a cascaded ASR→MT→TTS pipeline.
  - Target latency window: 2-3s.
  - Per Google's own July 2025 research blog — the only public technical
    description of the shipped feature.
- Presumed descendant of Google's published **Translatotron lineage**:
  - v1 — separate speaker-encoder network for voice preservation.
  - v2 — voice preservation folded into a shared attention/decoder,
    deliberately misuse-resistant.
  - v3 — unsupervised training. Confirmed via adversarial verification *not*
    to be Meet's architecture — lineage/prior art only.
  - **AudioPaLM** (PaLM-2 + AudioLM fusion) is the closest published relative
    to what the blog actually describes.
- **StreamSpeech** is the realistic open-source system in this space
  (MIT-licensed, pretrained checkpoints, runnable today) — but it's a
  **translation** model with no LLM and no slot for generating a novel
  reply, so it doesn't transfer to mirror.me-radio's use case.
- **Bottom line: this whole architecture (translation + voice preservation)
  is not what mirror.me-radio needs.** The one transferable idea — chunked
  streaming + a learned commit policy — reappears in the actually-relevant
  research, see `02-local-voice-agent-latency.md`.

## What Google Meet's live translation actually is

> "a streaming encoder that summarizes source audio from the preceding 10
> seconds and a streaming decoder that predicts translated audio
> autoregressively... builds on transformer blocks and the AudioLM
> framework."[^1]

- Only public technical description of the shipped feature — a company blog
  post, not a peer-reviewed paper. Treat architectural detail as thinner than
  the Translatotron/AudioPaLM papers below.
- Single end-to-end model, not a cascaded ASR→MT→TTS pipeline. No text
  intermediate at inference.
- Output is discrete AudioLM-style tokens, decoded autoregressively.
- Optimal latency window identified by Google's team: **2-3 seconds** —
  faster became hard to understand, slower hindered conversation flow.
- Voice preservation: output uses "a voice like yours," not a generic
  synthesized voice. Keeps tone and emotion, not just words — though it
  currently translates fairly literally (idiom/irony handling is a stated
  future improvement, not present yet).
- Real-world observed behavior (own experience, corroborating the
  chunk-based streaming description over the "2-3s per utterance" framing):
  starts producing translated speech ~1-2s into the person talking and keeps
  translating incrementally while they continue — chunked, continuous
  decoding, not one blocking wait-then-dump.

## The Translatotron lineage (Google's published prior art)

This is the well-documented research trail Meet's system is presumed to
build on — the blog doesn't disambiguate exactly which lineage feature
ships, so treat the connection as informed inference, not confirmed 1:1.

- **Translatotron (v1)**[^2] — original direct/no-intermediate-text
  speech-to-speech translation model. Maps spectrogram-to-spectrogram
  end-to-end "without relying on intermediate text representation."
  - Voice preservation from a **separate speaker-encoder network**,
    pretrained on the speaker-verification task, conditioning the output on
    the source speaker's timbre.
- **Translatotron 2**[^3] — single model trained end-to-end: speech encoder +
  linguistic decoder + acoustic synthesizer, all connected through **one
  shared attention module**.
  - Outperforms v1 by up to +15.5 BLEU, approaches cascade-system
    translation quality.
  - Voice preservation folded into that same attention/decoder mechanism
    (not a bolted-on cloning module), plus a training-time technique called
    **ConcatAug** — preserves each speaker's voice across turns in
    multi-speaker audio without needing runtime speaker segmentation.
  - Explicitly designed to **limit misuse as an arbitrary voice-cloning
    tool** — preserves the *source* speaker in *that* utterance, not a
    general-purpose cloning capability.
- **Translatotron 3**[^4] — extends v2's architecture to an **unsupervised**
  setting (monolingual data only, no parallel speech pairs).
  - Confirmed via adversarial verification to be lineage/prior art, not the
    architecture behind Meet's 2025 feature — explicitly checked and ruled
    out.

## AudioPaLM

- Fuses PaLM-2 (Google's text LLM) and AudioLM into one unified
  discrete-token multimodal architecture.[^5]
- Because it's built on AudioLM, **inherits AudioLM's ability to preserve
  paralinguistic information** — speaker identity, intonation — without a
  dedicated per-task module for it, and can transfer a voice across
  languages from a short spoken prompt.
- Architecturally the closest published relative to what the Meet blog post
  describes (transformer blocks + AudioLM framework) — though again, not
  confirmed to be literally the same model.

## Why cascaded pipelines are slow, and how streaming ones aren't

- Classic ASR→MT→TTS pipeline introduces 10-20s of latency because each
  stage waits for the previous one to fully finish: ASR waits for enough
  audio to finalize a transcript, MT waits for the complete transcript, TTS
  synthesizes from scratch afterward. Three sequential, largely
  non-overlapping waits, each carrying its own model-load/inference
  overhead, stacked serially.
- Streaming/simultaneous translation models collapse this by chunking the
  input (StreamSpeech, for example, uses 320ms chunks) and using a learned
  or monotonic **read/write policy** — wait-k, monotonic attention
  (variational monotonic multihead attention / V-MMA), or CTC-based
  alignment — so the decoder starts emitting translated audio before the
  source utterance has even finished, rather than blocking on a full
  transcript.
  - V-MMA.[^6]
  - SAT (self-adaptive training)[^7] confirms lower latency than cascaded
    baselines at matched BLEU for Zh↔En — but the stronger general claim
    "direct S2S always beats cascaded simultaneous baselines" was explicitly
    refuted in verification and should not be treated as a general law.

## StreamSpeech — the realistic open-source starting point (for translation, not conversation)

[github.com/ictnlp/StreamSpeech](https://github.com/ictnlp/StreamSpeech),
MIT-licensed, ACL 2024.[^8]

- A single multi-task-trained "All-in-One" model: streaming ASR, simultaneous
  speech-to-text translation, and speech-to-speech translation.
- Two-pass architecture: chunk-based Conformer streaming encoder → first
  pass autoregressive speech-to-text → second pass non-autoregressive
  text-to-unit generation.
- CTC-based alignment decoders (source/target/unit) learn when to start
  recognizing, translating, and synthesizing — this is the reusable idea, an
  alignment policy learned jointly rather than a hand-tuned wait-k rule.
- Ships pretrained checkpoints for Fr/Es/De↔En on Hugging Face
  (`ICTNLP/StreamSpeech_Models`) plus a HiFi-GAN vocoder checkpoint —
  runnable today without training.
- **Caveat, verified during adversarial checking:** the commonly-cited
  ~1.72s average latency figure at 320ms chunks was refuted on review (0-3
  vote) — don't cite that specific number as reliable.
- **Uses a fixed HiFi-GAN vocoder — no source-voice cloning.** Combining
  StreamSpeech's translation speed with voice preservation would need a
  from-scratch add-on (speaker-embedding conditioning on the vocoder stage,
  à la Translatotron 1, or a post-hoc voice-conversion pass).

## Why this doesn't apply directly to mirror.me-radio

StreamSpeech (and the whole lineage above) solves translation: input speech
in language A → output speech in language B, saying the same thing. There's
no LLM in it and no slot for generating a novel conversational response —
the output is a translation of what was said, not a reply to it. Repurposing
it for mirror.me-radio's narrator-conversation use case would mean gutting
the MT decoder and NAR unit-generation stage and keeping only the streaming
ASR front end — fighting a research-grade fairseq/PyTorch codebase built for
a different task, when a purpose-built local streaming ASR tool does that
job more directly (see `02-local-voice-agent-latency.md`). The one genuinely
transferable idea, chunk-based streaming plus a learned alignment/commit
policy, is the same conceptual trick needed for fast end-of-speech detection
in a conversational pipeline — just applied differently: endpointing, not
cross-lingual translation.

## Open questions (not resolved by this research pass)

- Google's blog doesn't publish measured latency/voice-preservation-quality
  numbers for the shipped Meet feature — only the architecture description
  and the "2-3s target window" design goal.
- Whether Meet's production model uses a Translatotron-2-style explicit
  speaker-conditioning attention mechanism or an AudioPaLM-style "inherited
  from AudioLM tokenization" approach is not disambiguated by the blog post.
- No source found that benchmarks voice-preservation quality vs. latency
  quantitatively across these systems side by side.

## Sources

[^1]: Google research blog, "Real-time speech-to-speech translation" (July 2025) — https://research.google/blog/real-time-speech-to-speech-translation/
[^2]: Translatotron (v1) — https://research.google/blog/introducing-translatotron-an-end-to-end-speech-to-speech-translation-model/
[^3]: Translatotron 2 — arXiv:2107.08661 — https://arxiv.org/abs/2107.08661
[^4]: Translatotron 3 — arXiv:2305.17547 — https://arxiv.org/pdf/2305.17547
[^5]: AudioPaLM — arXiv:2306.12925 — https://arxiv.org/abs/2306.12925
[^6]: V-MMA — arXiv:2110.08250 — https://arxiv.org/pdf/2110.08250
[^7]: SAT (self-adaptive training) — arXiv:2010.10048 — https://arxiv.org/pdf/2010.10048
[^8]: StreamSpeech — arXiv:2406.03049 — https://arxiv.org/abs/2406.03049
