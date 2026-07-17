import time
from pathlib import Path

from scipy.io import wavfile

from tts.interface import SynthResult


class MLXAudioTTS:
    """mlx-audio (Kokoro-82M) — MLX-native, fixed voice, no cloning."""

    def __init__(self, voice: str = "af_heart"):
        self.voice = voice
        self.model = "mlx-community/Kokoro-82M-bf16"

    @property
    def name(self) -> str:
        return f"mlx-audio-kokoro-{self.voice}"

    def synthesize(self, text: str, out_path: str) -> SynthResult:
        from mlx_audio.tts.generate import generate_audio

        start = time.perf_counter()
        generate_audio(
            text=text,
            model=self.model,
            voice=self.voice,
            file_prefix=out_path.removesuffix(".wav"),
            save=True,
            verbose=False,
        )
        latency_ms = (time.perf_counter() - start) * 1000

        # mlx-audio writes "{file_prefix}_000.wav", not out_path directly
        generated_path = out_path.removesuffix(".wav") + "_000.wav"
        Path(generated_path).rename(out_path)

        sample_rate, audio = wavfile.read(out_path)
        duration = len(audio) / sample_rate

        return SynthResult(
            text=text,
            audio_path=out_path,
            audio_duration_s=duration,
            latency_ms=latency_ms,
            provider=self.name,
        )
