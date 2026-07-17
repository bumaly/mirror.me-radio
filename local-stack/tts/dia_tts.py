import time
from pathlib import Path

from scipy.io import wavfile

from tts.interface import SynthResult


class DiaTTS:
    """Dia-1.6B (mlx-community) — MLX-native, single fixed speaker, supports
    inline non-verbal/emotion cues like (sighs), (laughs) in the text."""

    def __init__(self):
        self.model = "mlx-community/Dia-1.6B"

    @property
    def name(self) -> str:
        return "mlx-audio-dia-1.6b"

    def synthesize(self, text: str, out_path: str) -> SynthResult:
        from mlx_audio.tts.generate import generate_audio

        start = time.perf_counter()
        generate_audio(
            text=f"[S1] {text}",
            model=self.model,
            file_prefix=out_path.removesuffix(".wav"),
            save=True,
            verbose=False,
        )
        latency_ms = (time.perf_counter() - start) * 1000

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
