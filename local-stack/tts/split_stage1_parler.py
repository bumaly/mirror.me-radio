# Split-pipeline stage 1: expressive generation via Parler (performance donor).
# Voice identity doesn't matter here — stage 2 (OpenVoice converter) repaints
# timbre from the narrator reference. Only the delivery survives.
#
# Run with: .venv-parler/bin/python -m tts.split_stage1_parler

import json

from tts.parler_eval import EMOTIONS, synthesize
from tts.test_lines import LINES

# Static gap-filler assets — played while the real response generates.
FILLERS = [
    ("Hmm...", "thoughtful, trailing off"),
    ("Huh.", "surprised, soft"),
    ("That's a good question.", "curious, thinking out loud"),
    ("Give me a second.", "gentle, unhurried"),
    ("Mmm, let me think.", "soft, pondering"),
]


def main():
    results = []
    for i, (line, emotion) in enumerate(zip(LINES, EMOTIONS)):
        out_path = f"tts/synth_out/split_src_line{i}.wav"
        r = synthesize(line, emotion, out_path)
        results.append(vars(r))
        print(f"  [{r.latency_ms:7.0f}ms, {r.audio_duration_s:.1f}s] ({emotion})  {r.text}")

    for i, (line, emotion) in enumerate(FILLERS):
        out_path = f"tts/synth_out/split_src_filler{i}.wav"
        r = synthesize(line, emotion, out_path)
        results.append(vars(r))
        print(f"  [{r.latency_ms:7.0f}ms, {r.audio_duration_s:.1f}s] ({emotion})  {r.text}")

    with open("tts/synth_out/split_stage1.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  {len(results)} clips + timings -> tts/synth_out/split_stage1.json")


if __name__ == "__main__":
    main()
