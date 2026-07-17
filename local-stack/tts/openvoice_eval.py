# Standalone OpenVoice V2 eval — runs in its own venv (.venv-openvoice, Python 3.10).
#
# Two-stage: a base multilingual TTS (melo) speaks the line in a stock voice,
# then OpenVoice's tone-color converter re-colors it to match the reference clip.
#
# Requires a reference clip at tts/voices/narrator_ref.wav (15-20s, clean).
# First run downloads OpenVoice V2 checkpoints (~500MB) to tts/voices/checkpoints_v2/.
#
# Run with: .venv-openvoice/bin/python -m tts.openvoice_eval

import time
from pathlib import Path

import torch
from openvoice import se_extractor
from openvoice.api import ToneColorConverter

from tts.interface import SynthResult
from tts.test_lines import LINES

REF_AUDIO = "tts/voices/narrator_ref.wav"
CKPT_DIR = "tts/voices/checkpoints_v2/converter"
device = "mps" if torch.backends.mps.is_available() else "cpu"

converter = ToneColorConverter(f"{CKPT_DIR}/config.json", device=device)
converter.load_ckpt(f"{CKPT_DIR}/checkpoint.pth")

target_se, _ = se_extractor.get_se(REF_AUDIO, converter, vad=False)

from melo.api import TTS as MeloTTS

base_tts = MeloTTS(language="EN", device=device)
speaker_id = base_tts.hps.data.spk2id["EN-Default"]
source_se = torch.load(
    f"{CKPT_DIR}/../base_speakers/ses/en-default.pth", map_location=device
)


def synthesize(text: str, out_path: str) -> SynthResult:
    start = time.perf_counter()
    tmp_path = out_path.replace(".wav", "_base.wav")
    base_tts.tts_to_file(text, speaker_id, tmp_path, speed=1.0)
    converter.convert(
        audio_src_path=tmp_path,
        src_se=source_se,
        tgt_se=target_se,
        output_path=out_path,
    )
    latency_ms = (time.perf_counter() - start) * 1000

    import soundfile as sf

    audio, sr = sf.read(out_path)
    duration = len(audio) / sr

    return SynthResult(
        text=text,
        audio_path=out_path,
        audio_duration_s=duration,
        latency_ms=latency_ms,
        provider="openvoice-v2",
    )


def main():
    if not Path(REF_AUDIO).exists():
        print(f"Missing reference clip at {REF_AUDIO} — record one first.")
        return

    print(f"Evaluating {len(LINES)} lines on openvoice-v2\n")
    total_latency = 0.0
    total_audio = 0.0
    for i, line in enumerate(LINES):
        out_path = f"tts/synth_out/openvoice-v2_{i}.wav"
        r = synthesize(line, out_path)
        total_latency += r.latency_ms
        total_audio += r.audio_duration_s
        print(f"  [{r.latency_ms:7.0f}ms, {r.audio_duration_s:.1f}s audio]  {r.text}")

    rtf = (total_latency / 1000) / total_audio
    print(f"\n  avg latency: {total_latency / len(LINES):.0f}ms per line")
    print(f"  real-time factor: {rtf:.2f}x  (below 1.0 = faster than real time)\n")


if __name__ == "__main__":
    main()
