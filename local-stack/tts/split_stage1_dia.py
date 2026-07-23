# Split-pipeline stage 1, Dia variant: expressive generation via Dia-1.6B.
# Dia takes inline non-verbal cues, not a style prompt — expressiveness is
# steered per line with markup. Appends to split_stage1.json so stage 2
# converts both Parler and Dia clips in one pass.
#
# Run with: uv run python -m tts.split_stage1_dia

import json
from pathlib import Path

from tts.dia_tts import DiaTTS
from tts.test_lines import LINES

# Per-line expressive markup mirroring parler_eval's EMOTIONS.
MARKED_LINES = [
    "Hi... (pause) is someone there?",
    "My mum says it's nothing... (sighs) but it makes my tummy hurt.",
    "They're loud and mean, like someone is yelling at me but I don't know who.",
    "(sighs) I don't know why he doesn't come home very much.",
    "You don't have to be scared. I'm not going anywhere.",
    "(laughs) Today we built a blanket fort and it was the best fort in the whole world!",
    "The bus picks me up at eight and drops me off at three.",
]

FILLERS = [
    "Hmm...",
    "Huh.",
    "That's a good question.",
    "Give me a second.",
    "Mmm... (pause) let me think.",
]


def main():
    assert len(MARKED_LINES) == len(LINES)
    tts = DiaTTS()
    stage1_path = Path("tts/synth_out/split_stage1.json")
    results = json.loads(stage1_path.read_text()) if stage1_path.exists() else []
    # ponytail: re-running replaces prior dia entries instead of duplicating
    results = [r for r in results if r["provider"] != tts.name]

    for prefix, lines in [("line", MARKED_LINES), ("filler", FILLERS)]:
        for i, line in enumerate(lines):
            out_path = f"tts/synth_out/split_src_dia_{prefix}{i}.wav"
            r = tts.synthesize(line, out_path)
            results.append(vars(r))
            print(f"  [{r.latency_ms:7.0f}ms, {r.audio_duration_s:.1f}s]  {r.text}")

    stage1_path.write_text(json.dumps(results, indent=2))
    print(f"\n  {len(results)} total clips in {stage1_path}")


if __name__ == "__main__":
    main()
