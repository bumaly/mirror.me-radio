# v1.0 Performance Notes

## Pipeline Latency
The full pipeline (Whisper → GPT-4o → ElevenLabs) runs sequentially and synchronously on the server. Observed breakdown:

- **Transcription (Whisper):** ~1–2s for short clips (5–15s of speech)
- **Rewrite (GPT-4o):** ~1–3s depending on prompt length and response length
- **Synthesis (ElevenLabs `eleven_flash_v2_5`):** ~1–3s — flash model chosen specifically for lower latency
- **Total round-trip:** typically 4–8s from send to audio playback

Timings are measured server-side and returned with each response. They are displayed in the UI footer.

## Voice Cloning
- ElevenLabs IVC creates a usable clone from ~30–60s of clean speech
- Quality improves with longer, more varied samples
- Clone is created once per session; no fine-tuning or persistence across sessions

## Audio Format
- Recording: browser MediaRecorder outputs WebM/Opus or WAV depending on browser
- Sent to server as-is; Whisper handles most common formats
- TTS output: MP3 at 44.1kHz / 128kbps (`mp3_44100_128`)
- Returned as base64 and decoded client-side for immediate playback

## Known Constraints (v1.0)
- Session state is in-memory; restarting the server clears the voice profile
- Single-user only — no multi-session support; concurrent use will corrupt state
- No streaming — full audio must be synthesized before playback begins
- No error recovery for partial API failures mid-pipeline
- Voice samples are saved as temp files and deleted immediately after cloning
