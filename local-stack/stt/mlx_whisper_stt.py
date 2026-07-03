import time

import mlx_whisper
from scipy.io import wavfile

from stt.interface import TranscriptResult


class MLXWhisperSTT:
    def __init__(self, model_size: str = "medium"):
        self.model_size = model_size
        self.repo = f"mlx-community/whisper-{model_size}-mlx"

    @property
    def name(self) -> str:
        return f"mlx-whisper-{self.model_size}"

    def transcribe(self, wav_path: str) -> TranscriptResult:
        sample_rate, audio = wavfile.read(wav_path)
        duration = len(audio) / sample_rate

        start = time.perf_counter()
        result = mlx_whisper.transcribe(wav_path, path_or_hf_repo=self.repo)
        latency_ms = (time.perf_counter() - start) * 1000

        return TranscriptResult(
            text=result["text"].strip(),
            language=result["language"],
            audio_duration_s=duration,
            latency_ms=latency_ms,
            provider=self.name,
        )