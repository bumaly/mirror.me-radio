# MirrorMe: Radio — Architecture Spec (v1)

**Date:** 2026-04-28 (updated 2026-04-30)
**Status:** Pre-implementation — approved design decisions, ready to build
**Context:** Sit-down experience (not gallery installation)

---

## Concept

A virtual vintage radio with a tunable dial. The user searches through static to find hidden frequencies. Each frequency they discover takes them to the next chapter of a life — from infancy through old age. At each chapter, they speak into their microphone and hear their own voice returned to them, distorted through the inner critic of depression. The distortion is bidirectional: compassion softens it, aggression sharpens it. Eventually, the voice stops responding entirely. The radio goes silent. A narrator closes the experience.

---

## Experience Flow

### 1. Intro (Narrator)
- Distinct warm pre-recorded voice introduces the experience
- Brief framing: what the radio is, what the user should do (tune the dial, speak when they find a signal)
- During intro, the dial is inactive

### 2. Calibration (integrated into intro)
- During the intro/orientation clip, the narrator speaks to the user and invites them to respond
- The user's response is captured as the voice clone sample (~10+ seconds of natural speech)
- Audio is sent to ElevenLabs for voice cloning while the intro continues or transitions
- Visual: the radio warms up — tubes glow, needle trembles, static crackles
- The base voice model is created; DSP post-processing generates age variants
- **TBD:** Exact narrator prompt that elicits enough natural speech for a good clone

### 3. The Search (Core Loop)
- The dial becomes active across an FM-style band (e.g., 88.0–108.0 MHz)
- **Only 1 hot frequency is active at a time** — the user must find it among static
- Everything else is noise; the user tunes the dial searching for the signal
- When they land on the hot frequency, the static clears and the current chapter begins
- **Dial sensitivity narrows as chapters progress** — the lock-on zone shrinks, making later life stages harder to find:
  - Chapter 1 (infancy–tween): ±0.5 MHz lock-on zone
  - Chapter 2 (20s): ±0.4 MHz
  - Chapter 3 (30–40s): ±0.3 MHz
  - Chapter 4 (60s): ±0.2 MHz
  - Chapter 5 (80s): ±0.1 MHz (very precise tuning required)
  - Listen-only segments: ±0.3 MHz (moderate)
- After a chapter closes, the next frequency is placed semi-randomly — **must be at least 5 MHz away from the previous frequency** to prevent easy discovery
- Between chapters, the backend uses the transition time to adapt the voice clone and prepare the next chapter's prompts based on how the last exchange went

### 4. Chapters (Interactive Frequencies)
- Chapters are experienced in fixed narrative order regardless of which frequency the user finds
- At each chapter, the user speaks and the voice responds through the current distortion lens
- **Chapter resolution is adaptive:**
  - If the user speaks with compassion and comforts the voice → the chapter *resolves* (the voice softens, finds peace, and the chapter ends on a note of connection)
  - If the user does not comfort the voice → after a natural window where comfort would be expected, the chapter continues for ~3 more exchanges, then **the voice dismisses the user** without resolution
- Dismissals are age-appropriate:
  - Infancy–tween: *"I don't want to talk to you anymore"*
  - 20s: *"Just leave me alone"*
  - 30–40s: *"You wouldn't understand"*
  - 60s: *"There's nothing left to say"*
  - 80s: trails off mid-sentence, fades to static
- Once a chapter ends (resolved or dismissed), that frequency goes dead and cannot be revisited
- The next chapter's frequency loads into a new position on the dial

### 5. Listen-Only Frequencies (Narrative Segments)
- Listen-only segments appear **sequentially as part of the narrative**, interspersed between chapters
- Content is **pre-recorded narrative** — not ambient soundscapes — that advances the story
- When the user finds a listen-only frequency, a **white light** appears on the radio to signal it is a listening moment
- The audio **cannot be interrupted** — if the user speaks over it, nothing happens; the narrative plays to completion
- Once finished, the frequency goes dead and the next chapter frequency loads
- These do NOT advance the chapter counter — they are narrative bridges between life stages

### 6. Closing
- After all frequencies are exhausted (or after the final chapter), silence
- The narrator's voice returns with a closing statement
- The radio powers down visually — glow fades, needle drops to zero

---

## Narrative Sequence Map

The experience plays out in this fixed order. Only one frequency is active at a time.

| Step | Type | Content | Lock-on | Voice Model | Light |
|---|---|---|---|---|---|
| 0 | Narrator | Intro + calibration | N/A (auto) | Pre-recorded warm voice | — |
| 1 | Chapter | Infancy–Tween | ±0.5 MHz | voice_child (high pitch, fast) | Normal glow |
| 2 | Listen-only | Narrative bridge | ±0.3 MHz | Pre-recorded narration | White light |
| 3 | Chapter | 20s | ±0.4 MHz | voice_young (slight pitch up) | Normal glow |
| 4 | Chapter | 30–40s | ±0.3 MHz | voice_mid (baseline clone) | Normal glow |
| 5 | Listen-only | Narrative bridge | ±0.3 MHz | Pre-recorded narration | White light |
| 6 | Chapter | 60s | ±0.2 MHz | voice_mature (lower, slower) | Normal glow |
| 7 | Chapter | 80s | ±0.1 MHz | voice_elder (low, slow, fragile) | Normal glow |
| 8 | Narrator | Outro / closing | N/A (auto) | Same pre-recorded warm voice | — |

**Frequency placement:** Each step loads its frequency semi-randomly within 88.0–108.0 MHz, constrained to be at least 5 MHz away from the previous step's frequency.

**v2 consideration:** Test fixed frequency placement for fine-tuned search difficulty per stage.

---

## Audio Pipeline

```
Mic (WebAudio API)
  → Stream audio to backend via WebSocket
    → Whisper (local or API) — transcription
      → GPT-4o — dual output:
          1. Rewritten text (through current distortion lens)
          2. Compassion score (0.0–1.0)
          3. Aggression flag (boolean or score)
        → ElevenLabs — voice clone synthesis
          → Select age-appropriate voice model
          → Generate speech audio
            → Stream back to frontend via WebSocket
              → Playback through radio speaker UI
```

**Latency budget:** ~2–5 seconds end-to-end. During this gap: radio static audio + warm glow animation on the dial.

---

## Compassion State Machine

Tracked per chapter with **adaptive carryover** between chapters (GMAT-style). Each chapter starts at the harsh critic baseline, but a global compassion modifier carries forward — if the user was compassionate in earlier chapters, later chapters start slightly softer. If they were aggressive, later chapters start slightly harsher.

### Score Mechanics

- Each user utterance is scored by GPT-4o for compassion (0.0–1.0) and aggression (0.0–1.0)
- Running score uses exponential moving average: `score = α * new_score + (1 - α) * old_score`
- Decay: score drifts toward 0.3 (harsh baseline) during silence at rate β per second
- Score is clamped to [0.0, 1.0]
- **Global modifier:** `global_compassion` tracks a running average across all chapters. Each new chapter's starting score = `0.3 + (global_compassion - 0.3) * 0.3` — a dampened echo of the user's overall warmth (or coldness)

### Distortion Bands

| Score Range | State | Inner Critic Behavior |
|---|---|---|
| 0.0–0.2 | Vicious | Cruel, cutting, personal attacks. Voice is harsh, loud, fast |
| 0.2–0.4 | Harsh (default start) | Standard inner critic — self-doubt, catastrophizing, "you always..." |
| 0.4–0.6 | Softening | Less absolute language, more questioning than accusing |
| 0.6–0.8 | Balanced | Realistic self-talk, acknowledges difficulty without cruelty |
| 0.8–1.0 | Compassionate | Gentle, encouraging, warm. The voice the user could have for themselves |

### Aggression Reactivity (New)

- If the user speaks aggressively (harsh tone, hostile words), the score drops faster than natural decay
- GPT-4o prompt shifts to match: more personal, more cutting, mirrors the user's energy back at them
- ElevenLabs delivery parameters shift: faster speech rate, higher intensity, clipped phrasing
- The radio is a mirror — it gives back what it receives

### GPT-4o Prompt Structure

```
System: You are the inner voice of a {age_description} person experiencing depression.
Current distortion level: {state_name} (score: {score}).
The user just said: "{transcription}"
Their tone was: {aggressive|neutral|warm|compassionate}

Rewrite their statement as this inner voice would distort it.
At level "vicious": be cruel, personal, absolute.
At level "compassionate": be gentle, realistic, kind.
Match the distortion to the current level.

Also return:
- compassion_score: 0.0-1.0 (how compassionate was the user's utterance)
- aggression_score: 0.0-1.0 (how aggressive was the user's tone/words)

Return JSON: {"voice_text": "...", "compassion_score": 0.X, "aggression_score": 0.X}
```

---

## Voice Aging (v1: Clone + DSP)

### Approach
1. Single voice clone created during calibration via ElevenLabs
2. Age variants created via DSP post-processing on the synthesized audio:

| Life Stage | Pitch Shift | Speed | Formant | Character |
|---|---|---|---|---|
| Infancy–Tween | +4 semitones | 1.15x | +2 | Bright, quick, small |
| 20s | +1 semitone | 1.05x | +0.5 | Slightly young |
| 30–40s | 0 (baseline) | 1.0x | 0 | Natural clone |
| 60s | -2 semitones | 0.9x | -1 | Deeper, measured |
| 80s | -3 semitones | 0.8x | -2 | Low, slow, frail, slight tremor |

3. DSP applied server-side using `pydub` or `librosa` before streaming to frontend

### v2 Consideration
Test training multiple ElevenLabs voice models per user if single-clone + DSP sounds too artificial.

---

## Tech Stack

### Frontend
- **HTML/CSS/JS** — single-page app, no framework needed for v1
- **WebAudio API** — mic capture, playback, static generation
- **WebSocket** — real-time communication with backend
- **Visual:** vintage radio UI (functional first, styled later)
  - Tunable dial (knob or slider mapped to 88.0–108.0)
  - Frequency display
  - Glow indicator (processing state)
  - Speaker grille area (visual feedback during playback)

### Backend
- **FastAPI** with WebSocket support
- **Session state** — in-memory dict per connected client:
  ```python
  session = {
      "voice_clone_id": str,           # ElevenLabs voice ID
      "narrative_sequence": [dict],     # ordered list of steps (chapters + listen-only)
      "current_step_index": int,        # which step in the narrative (0-8)
      "active_frequency": float,        # current hot frequency on the dial
      "previous_frequency": float,      # last frequency (for spacing constraint)
      "lock_on_radius": float,          # current lock-on zone (shrinks over time)
      "global_compassion": float,       # GMAT-style carryover score
      "current_chapter": {
          "life_stage": str,
          "compassion_score": float,
          "exchange_count": int,
          "comfort_window_passed": bool, # has the natural comfort window elapsed?
          "exchanges_since_window": int,  # exchanges after comfort window (max ~3)
          "resolved": bool,              # did the user comfort the voice?
          "dismissed": bool
      }
  }
  ```

### APIs
- **OpenAI Whisper** — transcription (local or API)
- **OpenAI GPT-4o** — rewrite + scoring (API)
- **ElevenLabs** — voice clone creation + TTS synthesis (API)

### Audio Assets (Pre-recorded)
- Narrator intro/outro (distinct warm voice)
- 2 narrative bridge segments (listen-only, pre-recorded)
- Radio static loop (generated or recorded)
- Dismissal lines per life stage (synthesized from clone at build time, or generated live)

---

## WebSocket Protocol

### Client → Server

```json
{"type": "calibrate", "audio": "<base64 PCM>"}
{"type": "tune", "frequency": 94.7}
{"type": "speak", "audio": "<base64 PCM>"}
```

### Server → Client

```json
{"type": "calibration_complete", "ready": true}
{"type": "frequency_loaded", "lock_on_radius": 0.4}
{"type": "frequency_status", "status": "static|listen_only|chapter", "life_stage": "20s"}
{"type": "listen_only_start", "audio": "<base64 or URL>", "indicator": "white_light"}
{"type": "listen_only_end"}
{"type": "processing", "started": true}
{"type": "voice_response", "audio": "<base64>", "compassion_score": 0.4, "state": "harsh"}
{"type": "chapter_resolved", "life_stage": "20s", "resolution_audio": "<base64>"}
{"type": "chapter_dismissed", "life_stage": "20s", "dismissal_audio": "<base64>"}
{"type": "experience_complete"}
```

---

## Resolved Decisions

1. **Dial sensitivity:** Narrows as chapters progress. ±0.5 MHz for first chapter down to ±0.1 MHz for the last. Finding later life stages requires precise, patient tuning.
2. **Listen-only placement:** Sequential as part of the narrative. Appear between chapters as narrative bridges. White light visual indicator on the radio.
3. **Chapter resolution:** Adaptive. If the user comforts the voice → resolves peacefully. If not → ~3 more exchanges past the natural comfort window, then dismissal without resolution.
4. **Compassion carryover:** Yes — GMAT-style global modifier carries across chapters. Sustained warmth makes later chapters start slightly softer; sustained aggression makes them start harsher.
5. **Context:** Sit-down experience (not gallery). No timeout or attract mode needed.
6. **Calibration:** Integrated into the intro — user speaks to the narrator during the orientation clip, providing natural voice sample for cloning. Exact narrator prompt TBD.
7. **Frequency loading:** One at a time. After each chapter/listen-only ends, the next frequency loads ≥5 MHz away from the previous.

## Remaining Open Questions

1. **Calibration prompt:** What does the narrator say to elicit ~10 seconds of natural speech from the user? Needs to feel thematic, not clinical.
2. **Narrative bridge content:** What story do the 2 listen-only segments tell? How do they connect to the chapters before and after them?
3. **Resolution vs. dismissal feel:** What does a resolved chapter sound like? A sigh of relief? The voice saying something grateful? How different is the emotional texture from a dismissal?
4. **DSP tuning:** The pitch/speed/formant values in the Voice Aging table are starting guesses. Need real testing with actual voice samples.
5. **Lock-on sensitivity values:** ±0.5 down to ±0.1 are guesses. Real-world dial UX testing needed — too narrow and it's frustrating, too wide and there's no challenge.

---

## Implementation Order

1. **Backend skeleton** — FastAPI + WebSocket, session state, frequency generation
2. **Frontend skeleton** — Radio UI with tunable dial, WebSocket connection
3. **Calibration flow** — Mic capture → ElevenLabs clone creation
4. **Core loop** — Tune → detect hot frequency → Whisper → GPT-4o → ElevenLabs → playback
5. **Compassion state machine** — Scoring, state transitions, prompt shifting
6. **Aggression reactivity** — Bidirectional scoring, tone matching
7. **DSP aging** — Post-processing pipeline per life stage
8. **Dismissal mechanic** — Exchange counting, dismissal lines, frequency death
9. **Listen-only segments** — Narrative bridge playback, white light indicator, non-interruptible audio
10. **Narrator bookends** — Intro/outro playback
11. **Polish** — Static generation, glow animations, visual feedback
