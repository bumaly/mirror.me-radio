# MirrorMe: Radio — v0 Playtest Notes

**Date:** 2026-04-30
**Build:** v0 (dial + discovery)

---

## What Works
- Core mechanic: dial tuning, one-at-a-time frequency, static → lock-on → chapter text
- White light indicator for listen-only segments
- Static audio present and functional
- Radio metaphor reads: it's a radio with a dial, there's a screen for text

## Issues to Fix (v0.1)

### 1. Tuning is too easy
- Lock-on zones are too wide — user finds hot frequencies almost immediately
- **Fix options (try both):**
  - A) Narrow all lock-on radii (e.g. halve them: ±0.25 down to ±0.05)
  - B) Shorter dial throw — more physical rotation needed to cover the same MHz range, so the user has to turn more to sweep the band
  - C) Both

### 2. No proximity feedback ("tuning" visuals)
- Currently snaps from pure static → locked on with no in-between
- **Want:** graduated feedback as user gets close to a hot frequency:
  - Static begins to thin / crackle differently
  - Visual hint — maybe the static on the speaker grille starts to pattern, or the indicator light flickers faintly
  - Audio: mix in a faint tone or hum underneath the static that gets stronger as you approach
  - Creates a "warmer... warmer... HOT" feel

### 3. Lock-on snap is too abrupt
- Related to #2 — when you hit the frequency, it jumps straight to the chapter
- **Want:** a brief "tuning in" transition (300–500ms) where the static fades, maybe a brief radio-tuning sweep sound, then the chapter begins

### 4. Visual design (deferred to full frontend pass)
- Too dark overall
- Doesn't look like a realistic radio — more like a dark UI panel
- Acceptable for now, full visual redesign planned for later
- Future direction: more realistic vintage radio — bakelite texture, warm wood, visible tubes, physical-feeling knobs

## v2 Reminders
- Test fixed frequency placement (vs random) for fine-tuned search difficulty
