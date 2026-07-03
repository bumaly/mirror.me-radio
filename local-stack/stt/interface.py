from dataclasses import dataclass


@dataclass
class TranscriptResult:
    text: str            # what was said
    language: str        # detected language, e.g. "en", "es"
    audio_duration_s: float   # length of the clip
    latency_ms: float    # how long transcription took
    provider: str        # which model produced this