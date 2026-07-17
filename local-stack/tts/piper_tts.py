import time
import wave

from tts.interface import SynthResult


class PiperTTS:
    """Piper — ONNX/CPU, fixed voice, no cloning. Requires a downloaded .onnx voice model."""

    def __init__(self, model_path: str):
        self.model_path = model_path

    @property
    def name(self) -> str:
        return f"piper-{self.model_path.split('/')[-1].removesuffix('.onnx')}"

    def synthesize(self, text: str, out_path: str) -> SynthResult:
        from piper import PiperVoice

        voice = PiperVoice.load(self.model_path)

        start = time.perf_counter()
        with wave.open(out_path, "wb") as wav_file:
            voice.synthesize_wav(text, wav_file)
        latency_ms = (time.perf_counter() - start) * 1000

        with wave.open(out_path, "rb") as wav_file:
            duration = wav_file.getnframes() / wav_file.getframerate()

        return SynthResult(
            text=text,
            audio_path=out_path,
            audio_duration_s=duration,
            latency_ms=latency_ms,
            provider=self.name,
        )
