# Split-pipeline stage 2: tone-color conversion. Takes stage 1's expressive
# Parler clips and re-colors them to the narrator reference voice. Source
# embedding is extracted per-clip (Parler's voice drifts between generations).
#
# Run with: .venv-openvoice/bin/python -m tts.split_stage2_convert

import json
import time
from pathlib import Path

import torch
from openvoice.api import ToneColorConverter

REF_AUDIO = "tts/voices/narrator_ref.wav"
CKPT_DIR = "tts/voices/checkpoints_v2/converter"
device = "mps" if torch.backends.mps.is_available() else "cpu"

converter = ToneColorConverter(f"{CKPT_DIR}/config.json", device=device)
converter.load_ckpt(f"{CKPT_DIR}/checkpoint.pth")
target_se = converter.extract_se(REF_AUDIO)


def main():
    stage1 = json.load(open("tts/synth_out/split_stage1.json"))
    print(f"Converting {len(stage1)} clips to narrator voice (device={device})\n")

    rows = []
    for r in stage1:
        src = r["audio_path"]
        out = src.replace("split_src_", "split_parler_")
        start = time.perf_counter()
        source_se = converter.extract_se(src)
        converter.convert(
            audio_src_path=src, src_se=source_se, tgt_se=target_se, output_path=out
        )
        convert_ms = (time.perf_counter() - start) * 1000
        total_ms = r["latency_ms"] + convert_ms
        rows.append((r["text"], r["latency_ms"], convert_ms, total_ms, r["audio_duration_s"]))
        print(f"  [gen {r['latency_ms']:6.0f}ms + conv {convert_ms:5.0f}ms = {total_ms:6.0f}ms, "
              f"{r['audio_duration_s']:.1f}s]  {r['text']}")

    total_latency = sum(t for _, _, _, t, _ in rows)
    total_audio = sum(a for _, _, _, _, a in rows)
    print(f"\n  avg total latency: {total_latency / len(rows):.0f}ms per line")
    print(f"  pipeline RTF: {(total_latency / 1000) / total_audio:.2f}x")
    ttfa = min(t for _, _, _, t, _ in rows)
    print(f"  best-case time-to-first-audio (shortest clip): {ttfa:.0f}ms")


if __name__ == "__main__":
    main()
