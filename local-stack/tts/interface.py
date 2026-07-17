from dataclasses import dataclass


@dataclass
class SynthResult:
    text: str            # what was synthesized
    audio_path: str      # where the output wav was written
    audio_duration_s: float   # length of the generated clip
    latency_ms: float    # how long synthesis took
    provider: str        # which model produced this
