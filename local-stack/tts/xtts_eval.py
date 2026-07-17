# Standalone XTTS-v2 eval — runs in its own venv (.venv-xtts, Python 3.11)
# because coqui-tts pins deps incompatible with mlx-audio.
#
# Requires a reference clip at tts/voices/narrator_ref.wav (15-20s, clean).
#
# Run with: .venv-xtts/bin/python -m tts.xtts_eval

import time
from pathlib import Path

from TTS.api import TTS

from tts.interface import SynthResult
from tts.test_lines import LINES

REF_AUDIO = "tts/voices/narrator_ref.wav"

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")


def synthesize(text: str, out_path: str) -> SynthResult:
    start = time.perf_counter()
    tts.tts_to_file(
        text=text,
        speaker_wav=REF_AUDIO,
        language="en",
        file_path=out_path,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    import soundfile as sf

    audio, sr = sf.read(out_path)
    duration = len(audio) / sr

    return SynthResult(
        text=text,
        audio_path=out_path,
        audio_duration_s=duration,
        latency_ms=latency_ms,
        provider="xtts-v2",
    )


def main():
    if not Path(REF_AUDIO).exists():
        print(f"Missing reference clip at {REF_AUDIO} — record one first.")
        return

    print(f"Evaluating {len(LINES)} lines on xtts-v2\n")
    total_latency = 0.0
    total_audio = 0.0
    for i, line in enumerate(LINES):
        out_path = f"tts/synth_out/xtts-v2_{i}.wav"
        r = synthesize(line, out_path)
        total_latency += r.latency_ms
        total_audio += r.audio_duration_s
        print(f"  [{r.latency_ms:7.0f}ms, {r.audio_duration_s:.1f}s audio]  {r.text}")

    rtf = (total_latency / 1000) / total_audio
    print(f"\n  avg latency: {total_latency / len(LINES):.0f}ms per line")
    print(f"  real-time factor: {rtf:.2f}x  (below 1.0 = faster than real time)\n")


if __name__ == "__main__":
    main()
