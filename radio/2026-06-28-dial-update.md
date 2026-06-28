# MirrorMe: Radio — Dial Update

**Date:** 2026-06-28
**Branch:** feat/dial-dual-ring → merged to main

---

## What Changed

### Dual-ring scale
The dial has a 540° throw (1.5 full rotations). Previously all frequencies shared a single ring, making it impossible to distinguish first-turn (88–101.3 MHz) from second-turn (101.3–108 MHz) frequencies visually.

- **Inner ring** (r=66): full circle, shows 88 / 92 / 96 / 100 MHz — first rotation
- **Outer ring** (r=80): south semicircle arc (east→south→west), shows 104 / 108 MHz — second rotation
- **Radial bridge** at 101.3 MHz (east/3 o'clock position) marks where the second turn begins
- Split frequency: `88 + (360/540) × 20 = 101.333 MHz`

### Text clipping fix
Added `overflow="visible"` to the `#knob-scale` SVG. SVG clips to its viewBox by default; this was hiding labels near the edges. No layout changes needed — the parent div has no `overflow: hidden`.

### Label placement
Inner ring labels were at `rI - 17 = 49px` from center — hidden under the knob body (radius 53px). Moved to `rI + 10 = 76px`, sitting in the gap between the two rings.

### Knob color
Was near-black (`#152030 / #0A1520`). Updated to navy blue (`#2E5272 / #1A3448`) to fit the light blue palette while still reading as a distinct control.

### Layout
- `freq-col`: changed from `flex: 1` to `flex: 0 0 190px` — prevents the display from expanding into the dial label overflow zone
- `knob-col`: `margin-left: auto` — pushes knob to the right edge of the face
- `.rf-ctrl` gap: `14px → 28px`
- Radio width: back to `min(480px, 100vw)` — the layout changes made the earlier 560px expansion unnecessary
