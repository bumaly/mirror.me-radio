# Standalone Parler-TTS eval — runs in its own venv (.venv-parler, Python 3.9)
# because parler-tts pins transformers==4.46.1, incompatible with mlx-audio.
#
# Run with: .venv-parler/bin/python -m tts.parler_eval

import time

import soundfile as sf
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

from tts.interface import SynthResult
from tts.test_lines import LINES

# Fixed narrator voice description — consistent identity across all lines,
# only the emotional coloring changes per line below.
VOICE = "A young woman's voice, clear and close-mic'd, speaking at a measured pace with slight studio reverb."

# Per-line emotion appended to the voice description, matching each line's intent.
EMOTIONS = [
    "hesitant and uncertain",
    "quietly worried",
    "tense and a little scared",
    "confused and sad",
    "warm and reassuring",
    "bright and delighted",
    "flat and matter-of-fact",
]

device = "mps" if torch.backends.mps.is_available() else "cpu"
model = ParlerTTSForConditionalGeneration.from_pretrained("parler-tts/parler-tts-mini-v1").to(device)
tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-v1")


def synthesize(text: str, emotion: str, out_path: str) -> SynthResult:
    description = f"{VOICE} Tone: {emotion}."
    input_ids = tokenizer(description, return_tensors="pt").input_ids.to(device)
    prompt_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)

    start = time.perf_counter()
    generation = model.generate(input_ids=input_ids, prompt_input_ids=prompt_ids)
    latency_ms = (time.perf_counter() - start) * 1000

    audio = generation.cpu().numpy().squeeze()
    sr = model.config.sampling_rate
    sf.write(out_path, audio, sr)

    return SynthResult(
        text=text,
        audio_path=out_path,
        audio_duration_s=len(audio) / sr,
        latency_ms=latency_ms,
        provider="parler-tts-mini-v1",
    )


def main():
    print(f"Evaluating {len(LINES)} lines on parler-tts-mini-v1 (device={device})\n")
    total_latency = 0.0
    total_audio = 0.0
    for i, (line, emotion) in enumerate(zip(LINES, EMOTIONS)):
        out_path = f"tts/synth_out/parler-tts-mini-v1_{i}.wav"
        r = synthesize(line, emotion, out_path)
        total_latency += r.latency_ms
        total_audio += r.audio_duration_s
        print(f"  [{r.latency_ms:7.0f}ms, {r.audio_duration_s:.1f}s audio] ({emotion})  {r.text}")

    rtf = (total_latency / 1000) / total_audio
    print(f"\n  avg latency: {total_latency / len(LINES):.0f}ms per line")
    print(f"  real-time factor: {rtf:.2f}x  (below 1.0 = faster than real time)\n")


if __name__ == "__main__":
    main()
