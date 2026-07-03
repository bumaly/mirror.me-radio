import time

from faster_whisper import WhisperModel

from stt.interface import TranscriptResult


class FasterWhisperSTT:
    def __init__(self, model_size: str = "small"):
        self.model_size = model_size
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")

    @property
    def name(self) -> str:
        return f"faster-whisper-{self.model_size}"

    def transcribe(self, wav_path: str) -> TranscriptResult:
        start = time.perf_counter()
        segments, info = self.model.transcribe(wav_path)
        text = " ".join(seg.text.strip() for seg in segments)
        latency_ms = (time.perf_counter() - start) * 1000

        return TranscriptResult(
            text=text,
            language=info.language,
            audio_duration_s=info.duration,
            latency_ms=latency_ms,
            provider=self.name,
        )