# STT Decision — 2026-07-03

**Winner: mlx-whisper-small** (~305ms avg/clip, RTF 0.03x on M-series Air)

Evaluated on 20-clip corpus (EN + ES, varied length/volume/hesitancy):
- faster-whisper-tiny: fast (336ms) but real word errors ("trekking", "under lie 31")
- faster-whisper-small: accurate, 2138ms avg — 7x slower than MLX equivalent
- faster-whisper-medium: accurate, 6491ms avg — disqualified on latency
- mlx-whisper-small: accurate, 305ms avg — winner
- mlx-whisper-medium: unstable language detection (tl/ms/ko on EN clips),
  hallucinates on near-silence — disqualified on reliability

Notes for pipeline: filter near-silent utterances before STT (VAD false
triggers produced empty/hallucinated transcripts).