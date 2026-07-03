import queue
import time
from pathlib import Path

import numpy as np
import sounddevice as sd
import torch
from scipy.io import wavfile
from silero_vad import load_silero_vad

SAMPLE_RATE = 16000
CHUNK_SIZE = 512            # samples per chunk — Silero expects exactly 512 @ 16kHz
SPEECH_THRESHOLD = 0.5      # VAD probability above this = speech
SILENCE_DURATION = 2.0      # seconds of silence that ends an utterance
PRE_ROLL = 0.3              # seconds of audio kept from before speech started

OUT_DIR = Path("recordings")
OUT_DIR.mkdir(exist_ok=True)

model = load_silero_vad()
audio_q: queue.Queue[np.ndarray] = queue.Queue()


def callback(indata, frames, time_info, status):
    if status:
        print(f"[audio status] {status}")
    audio_q.put(indata[:, 0].copy())


def main():
    print("Listening... speak whenever. Ctrl+C to stop.")
    pre_roll_chunks = int(PRE_ROLL * SAMPLE_RATE / CHUNK_SIZE)
    silence_chunks_needed = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK_SIZE)

    ring_buffer: list[np.ndarray] = []      # pre-roll storage
    utterance: list[np.ndarray] = []
    in_speech = False
    silence_count = 0

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype="float32", blocksize=CHUNK_SIZE,
                        callback=callback):
        while True:
            chunk = audio_q.get()
            prob = model(torch.from_numpy(chunk), SAMPLE_RATE).item()

            if not in_speech:
                ring_buffer.append(chunk)
                if len(ring_buffer) > pre_roll_chunks:
                    ring_buffer.pop(0)
                if prob >= SPEECH_THRESHOLD:
                    in_speech = True
                    utterance = ring_buffer.copy()
                    utterance.append(chunk)
                    silence_count = 0
                    print("▶ speech detected...")
            else:
                utterance.append(chunk)
                if prob < SPEECH_THRESHOLD:
                    silence_count += 2
                    if silence_count >= silence_chunks_needed:
                        save(utterance)
                        in_speech = False
                        ring_buffer = []
                        utterance = []
                else:
                    silence_count = 0


def save(chunks: list[np.ndarray]):
    audio = np.concatenate(chunks)
    audio_int16 = (audio * 32767).astype(np.int16)
    fname = OUT_DIR / f"utterance_{time.strftime('%H%M%S')}.wav"
    wavfile.write(fname, SAMPLE_RATE, audio_int16)
    dur = len(audio) / SAMPLE_RATE
    print(f"■ saved {fname} ({dur:.1f}s)")


if __name__ == "__main__":
    main()