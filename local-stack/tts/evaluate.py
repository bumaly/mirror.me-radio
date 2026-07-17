from tts.dia_tts import DiaTTS
from tts.mlx_audio_tts import MLXAudioTTS
from tts.piper_tts import PiperTTS
from tts.test_lines import LINES

# Piper needs a downloaded .onnx voice model — point this at one before running,
# e.g. `en_US-lessac-medium.onnx` from https://github.com/rhasspy/piper/releases
PROVIDERS = [
    DiaTTS(),
]


def main():
    print(f"Evaluating {len(LINES)} lines × {len(PROVIDERS)} models\n")

    for tts in PROVIDERS:
        print(f"{'=' * 60}")
        print(f"MODEL: {tts.name}")
        print(f"{'=' * 60}")

        total_latency = 0.0
        total_audio = 0.0
        for i, line in enumerate(LINES):
            out_path = f"tts/synth_out/{tts.name}_{i}.wav"
            r = tts.synthesize(line, out_path)
            total_latency += r.latency_ms
            total_audio += r.audio_duration_s
            print(f"  [{r.latency_ms:6.0f}ms, {r.audio_duration_s:.1f}s audio]  {r.text}")

        rtf = (total_latency / 1000) / total_audio
        print(f"\n  avg latency: {total_latency / len(LINES):.0f}ms per line")
        print(f"  real-time factor: {rtf:.2f}x  (below 1.0 = faster than real time)\n")


if __name__ == "__main__":
    main()
