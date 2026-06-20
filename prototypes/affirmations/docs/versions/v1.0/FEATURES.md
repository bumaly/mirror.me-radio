# v1.0 Feature List

## Voice Cloning
- Participant records ~60s of natural speech using a guided in-app script
- Audio uploaded to ElevenLabs Instant Voice Cloning (IVC) via API
- Cloned voice ID stored in server session for the duration of the experience

## Core Pipeline
- Hold-to-speak recording in the browser via MediaRecorder API
- Pre-send review: shows recording duration, offers re-record or send
- Audio sent to Flask backend via multipart form POST
- Transcription via OpenAI Whisper (`whisper-1`)
- Rewrite via GPT-4o using the "personal" distortion lens
- Speech synthesis via ElevenLabs (`eleven_flash_v2_5`) in the cloned voice
- Audio returned as base64 MP3 and played back in-browser

## Distortion Lens
- Single lens: "personal" — a dry, clipped interior critical voice
- Deflates affirmations without arguing; leaves thoughts incomplete
- Trained on example pairs to match a specific register and logic
- Configured via system prompt to GPT-4o

## Prompts
Six affirmations covering:
1. Relationships and showing up for others
2. Body image and physical self-perception
3. Creative talent and self-trust
4. Healing and growth
5. Being loved completely
6. Belonging and the value of being alive

## UI / Experience Flow
- Participant name entry
- Voice profile setup with guided script displayed in main panel during recording
- Post-record state: prompts participant to create profile
- Prompt list in sidebar; each prompt is selectable
- Session state: hold-to-speak, review, send flow
- Completed prompts show stored transcript and replay button for review
- "Thank You" tab appears in sidebar on completion, navigates to artist statement
- End-of-experience screen with closing text
- Session export: saves all exchanges to timestamped JSON file

## Performance Timing
- Pipeline timings (transcribe / rewrite / synthesize / total) displayed per response
