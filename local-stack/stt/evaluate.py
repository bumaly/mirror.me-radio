import glob

from stt.faster_whisper_stt import FasterWhisperSTT
from stt.mlx_whisper_stt import MLXWhisperSTT

PROVIDERS = [
    FasterWhisperSTT("small"),
    MLXWhisperSTT("small"),
    MLXWhisperSTT("medium"),
]


def main():
    files = sorted(glob.glob("recordings/*.wav"))
    if not files:
        print("No recordings found.")
        return
    print(f"Evaluating {len(files)} clips × {len(PROVIDERS)} models\n")

    for stt in PROVIDERS:
        print(f"{'=' * 60}")
        print(f"MODEL: {stt.name}")
        print(f"{'=' * 60}")

        total_latency = 0.0
        total_audio = 0.0
        for f in files:
            r = stt.transcribe(f)
            total_latency += r.latency_ms
            total_audio += r.audio_duration_s
            short = f.split("/")[-1]
            print(f"  {short}  [{r.language}] {r.latency_ms:6.0f}ms  {r.text}")

        rtf = (total_latency / 1000) / total_audio  # real-time factor
        print(f"\n  avg latency: {total_latency / len(files):.0f}ms per clip")
        print(f"  real-time factor: {rtf:.2f}x  (below 1.0 = faster than real time)\n")


if __name__ == "__main__":
    main()
    