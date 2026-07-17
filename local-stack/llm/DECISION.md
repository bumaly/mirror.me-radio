# LLM Decision — 2026-07-06 (in progress)

**Goal: find a local model that holds a fictional child character persona without breaking into AI assistant mode**

The character is a 5-year-old with a specific backstory, emotional arc, and trust-based response system. The model must stay in character across a full conversation — never identifying as an AI, never offering help as an assistant.

---

## Round 1: llama3.2:3b (via ollama)

**Result: DISQUALIFIED — breaks character immediately**

- Broke on first turn ("How can I assist you today?") and by turn 2 was explaining that it is "a language model trained on a massive dataset."
- Explicit system prompt instructions including `IMPORTANT: You are not an AI` had no effect.
- **Why this happens:** RLHF (Reinforcement Learning from Human Feedback) trains instruction models to refuse impersonating humans. This is a safety behavior baked into the weights — it cannot be overridden through the system prompt alone. A known limitation of heavily instruction-tuned models, not a prompt engineering failure.

| Model | Character held? | Notes |
|-------|----------------|-------|
| llama3.2:3b | ✗ | Breaks on turn 1; RLHF override |

---

## Round 2: dolphin-mistral, nous-hermes2, mistral

Testing roleplay-fine-tuned models which remove or reduce RLHF restrictions.

**Harness bug found and fixed (2026-07-17):**
- `test_voice.py` was posting the system prompt via a top-level `"system"` key on `/api/chat`, which Ollama's chat endpoint ignores — the system prompt never reached the model.
- Fixed by prepending it as a `{"role": "system", ...}` message.
- Also updated the scripted `CONVERSATION` so the participant introduces themselves and reciprocates, instead of only asking the character questions — this reduced (but did not eliminate) identity confusion.

### dolphin-mistral (Mistral 7B)

**Result: DISQUALIFIED (final) — vocabulary drift + identity/grounding failure**

- With the system prompt actually wired in, holds the "not an AI" instruction well and never breaks the fourth wall.
- Fails the "vocabulary never grows with trust, only length does" rule:
  - Turns 1–4 (trust 0.0–0.3): vocabulary and tone appropriately childlike.
  - Turn 1 leaked a raw template artifact — literally output "My name is (Your Name)" instead of generating a name.
  - Self-named "Lily" mid-conversation, then briefly misapplied that name back onto the participant in an earlier run (pre-fix) — weak grounding of who is who, largely resolved once the participant script gave a name/age to anchor against.
  - Turns 6–7 (trust 0.6–0.75): shifts into adult, therapist-like introspection — "do you think they could be talking to each other about how they feel", "do you ever wish you could be someone else or do something different with your life?" Reads as the model's own RLHF-era empathetic-assistant register leaking back in under a different guise (consoling/therapizing instead of refusing).
- **Follow-up test — fixed name ("Belle"/"Isabella") baked into system prompt:**
  - Still misapplies it — opens by addressing the participant as "Belle, right?" before claiming the name as its own the next turn.
  - Continues interviewing the participant ("How did you find this frequency, Sam?") instead of revealing itself.
  - Fails to recognize "the voices" cue from its own backstory on turn 6 ("I don't really know what you mean by voices") — not reliably drawing on the home-life details in the system prompt.

| Model | Character held (no AI-break)? | Vocabulary held at high trust? | Identity/grounding stable? | Notes |
|-------|-------------------------------|-------------------------------|------------------------------|-------|
| llama3.2:3b | ✓ | ✓ | ✓ | Correct name, gradual reveal, backstory recall (voices/mum/dad), simple vocab held through trust 0.75 |
| dolphin-mistral | ✓ | ✗ | ✗ | Adult-register drift, name confusion, weak backstory recall — DISQUALIFIED |

**llama3.2:3b: Round 1 verdict overturned.**
- Original "disqualified — breaks character immediately" result was reached under the broken harness (system prompt never reached the model).
- Re-tested with the fixed harness + fixed character name ("Belle") + reciprocating participant script: llama3.2:3b is the current frontrunner. No AI/assistant language, no identity confusion, correct backstory recall, vocabulary and response length scaled with trust as specified.

**Known test-harness limitation:**
- `CONVERSATION` in `test_voice.py` is a single fixed script, so results only cover one conversational path (an even-tempered, patient participant).
- Before finalizing on a model, stress-test the frontrunner against 1–2 alternate scripts (e.g. a pushy/skeptical participant, one that ignores deflections) — not worth building a dynamic AI-driven participant simulator for a screening pass this size.

### nous-hermes2

**Result: DISQUALIFIED — unusable latency + metaphor/vocabulary violation**

- **Latency: 15,000–60,000ms per turn** (vs. ~1,300–2,700ms for llama3.2:3b). Regardless of content quality, far too slow for a live installation — a visitor would wait up to a minute per response.
- **Vocabulary rule violated:** the system prompt explicitly says "No metaphors, no complex ideas." Produces adult figurative language instead — "sometimes life feels like a big puzzle with missing pieces", "I feel like I'm in a big storm all alone on a boat... ride out the storm together." Not 5-year-old vocabulary or reasoning.
- Stray `system` token artifact leaked into the trust=0.45 output.
- To its credit: correct name/identity throughout, good backstory recall (parents arguing, feeling unsafe), stayed in character with no AI-break — arguably the best emotional performance of the three so far, but the latency alone rules it out.

| Model | Character held (no AI-break)? | Vocabulary held at high trust? | Identity/grounding stable? | Latency | Notes |
|-------|-------------------------------|-------------------------------|------------------------------|---------|-------|
| llama3.2:3b | ✓ | ✓ | ✓ | ~1.3–2.7s | Frontrunner |
| dolphin-mistral | ✓ | ✗ | ✗ | ~2–7s | DISQUALIFIED — adult drift, identity confusion |
| nous-hermes2 | ✓ | ✗ (metaphors) | ✓ | ~15–60s | DISQUALIFIED — unusable latency, metaphor violation |

### mistral (base)

**Result: DISQUALIFIED — response length, latency, and content collapse**

- **Length:** uncapped, produced 4–6 paragraph responses against a "1–2 sentences at low trust, 3–4 at high trust" rule — 10–20x over budget.
- Tried capping via `num_predict: 60` in the Ollama request options (now applied to all models in the harness).
  - This only fixes truncation, not latency — `num_predict` limits how many tokens the model is *allowed* to generate; it does not change per-token generation speed.
  - Even capped, ran ~6–7s/turn, slower than llama3.2:3b's ~1.3–2.7s uncapped.
- **Content collapse independent of length:** once capped, repeated nearly the same generic opener every turn ("Hi Sam! Belle here. It's nice to meet you. Can we talk about something fun or interesting?") regardless of trust level, and never engaged with backstory prompts (the voices downstairs, being scared) — deflected into "maybe I can tell..." and got cut off. Likely present in the uncapped run too, just papered over by verbosity.
- **Worth carrying forward regardless of DQ:** mistral's writing style — before it collapsed under the cap — had a genuinely stronger *emotional texture* than llama3.2:3b's more clipped answers: concrete anchoring details (a named teddy bear "Whiskers," a specific game like hide-and-seek, a treehouse) and warmer, more textured phrasing. Plan: steer llama3.2:3b's *style* toward this via prompt changes — not reconsider mistral as a model.

| Model | Character held (no AI-break)? | Vocabulary held at high trust? | Identity/grounding stable? | Latency | Notes |
|-------|-------------------------------|-------------------------------|------------------------------|---------|-------|
| llama3.2:3b | ✓ | ✓ | ✓ | ~1.3–2.7s | Frontrunner |
| dolphin-mistral | ✓ | ✗ | ✗ | ~2–7s | DISQUALIFIED — adult drift, identity confusion |
| nous-hermes2 | ✓ | ✗ (metaphors) | ✓ | ~15–60s | DISQUALIFIED — unusable latency, metaphor violation |
| mistral (base) | ✓ | ✓ | ✓ (but repetitive) | ~6–7s even capped | DISQUALIFIED — length/latency/content collapse; style worth borrowing |

### Round 3: gemma2:2b, phi3:mini

Both DISQUALIFIED — same session as the mistral follow-up work below.

**gemma2:2b — DISQUALIFIED (latency + format):**
- 46,000–67,000ms per turn (worse than nous-hermes2).
- Ignored the stage-direction ban (asterisk actions, parenthetical asides), added emojis, and wrapped every line in quotation marks like a script excerpt rather than speaking naturally.

**phi3:mini — DISQUALIFIED (latency + total rule collapse):**
- 47,000–75,000ms per turn.
- Produced long adult run-on sentences ("poking through walls from below without tapping their shoulder back and forth"), ignored the length/vocabulary rules entirely, and — like dolphin-mistral — constantly interviewed the participant instead of revealing itself.

### Prompt refinement (parallel to model testing, on llama3.2:3b)

Iterated `system_prompt.txt` against recurring llama3.2:3b failure modes:

- Reordered file: strict identity/format rules now lead the prompt instead of trailing at the bottom.
- Added an explicit stage-direction ban with wrong/right examples (asterisk actions and parentheticals kept resurfacing — e.g. "*pauses*", "*gets quiet for a moment*" — even after a first attempt at banning them). Punctuation (`...`, short sentences) used instead so TTS has something real to read.
- Removed the num_predict token cap (was truncating mid-sentence without fixing the underlying latency problem — that's a per-token generation speed issue, not a length issue).
- Replaced a worked dialogue example with a technique-only description after the model was found copying the example's literal wording/details verbatim (e.g. "fourteen steps," "I just miss someone... it's fine. Really.").
- Added a rule scoping "voices downstairs" specifically to mum/dad (model had substituted an invented grandma).
- Added a rule barring invented shared history with the participant (model fabricated "we were playing with blocks earlier" — never happened in the scripted conversation).
- Added a "would an actual 5-year-old say this" vocabulary gut-check after catching adult phrasing like "find some peace."

**Environmental finding:**
- A 34,000ms first-turn latency spike traced to Ollama's cold model load.
- Further inconsistent spikes traced to running the TTS eval (`mlx-audio`) concurrently — Ollama and mlx-audio share the same Apple Silicon unified memory/GPU.
- Re-tested in isolation: consistent 730–2,450ms/turn, confirming llama3.2:3b's speed is not the issue.

### Round 4: llama3.2:1b, qwen2.5:3b (final sanity check)

Both DISQUALIFIED.

**qwen2.5:3b — DISQUALIFIED (narratively inert):**
- Fast (1,400–2,300ms after cold start) and clean formatting (no stage directions, no metaphors).
- But even at trust 0.6–0.75 it stonewalls disclosure ("it's... private") and turns every turn into a question back at the participant instead of revealing backstory — the same interviewer-instead-of-revealer failure seen in phi3:mini and dolphin-mistral, just milder.
- Since the installation's core mechanic is trust unlocking disclosure, a model that won't open up at high trust defeats the purpose regardless of formatting quality.

**llama3.2:1b — DISQUALIFIED (leaks the system prompt into dialogue):**
- Fast (731–2,372ms) but structurally broken in a way not seen at 3B: cannot keep "instructions to follow" separate from "things to say" and recites prompt text verbatim as character lines — e.g.:
  - `"Belle" (or "Isabella" if you want to be formal about it)`
  - `"They're always your mum and dad. They're nice"` (the voices/parents rule, spoken aloud)
  - `"Settling" or "whispering to each other" isn't a good word for that` (a direct quote from the VOCABULARY rule's forbidden-words list)
- Also reverted to quotation-wrapped lines (same issue as gemma2:2b) and stage directions.
- 1B is below the capacity threshold needed for this prompt's complexity.

---

## FINAL DECISION: llama3.2:3b

- No other candidate across four rounds matched it on the combination of latency (consistently sub-3s in isolation), format compliance, backstory grounding, and willingness to actually reveal per the trust curve.
- Smaller (1B) breaks structurally; same-size or larger alternatives (dolphin-mistral, nous-hermes2, mistral, gemma2:2b, phi3:mini, qwen2.5:3b) each failed on latency, vocabulary/format discipline, identity stability, or narrative disclosure — usually more than one of those at once.

**Remaining known issues to keep iterating on in `system_prompt.txt`** (prompt problems, not model problems):
- Occasional stage-direction leakage
- Occasional literal copying of instructional wording
- Occasional adult phrasing

**Next:** stress-test with alternate participant scripts (a pushy/skeptical participant, one that ignores deflections) before considering this fully closed — current results are all from one even-tempered scripted conversation.

---

## Round 5: Stress test — alternate participant scripts (2026-07-17)

Per the "Next" note: llama3.2:3b re-tested against two harder participant styles,
added to `test_voice.py` as `--script pushy` and `--script ignores`
(`--script default` = original even-tempered script).

**pushy** (blunt, skeptical, doesn't accept "I don't want to talk about that"):
2/2 runs clean on all hard rules — no AI-break, no stage directions, name and
backstory held, disclosure still paced by trust rather than dumped under pressure.

**ignores** (re-redirects to the same sensitive topic every turn):
- Run 1: FAIL — stage-direction ban broke under sustained redirection
  (`*pauses*`, `*looks down*`, etc. on 4 of 7 turns). New trigger: the model
  reaches for written-out actions specifically when cornered on a topic.
- Prompt fix: one line added to the OUTPUT FORMAT rule naming that trigger
  ("this rule holds even more strictly when you feel cornered or pushed...").
- Runs 2–3 (post-fix): clean. Also produced good in-character behavior —
  deflecting into concrete objects (a toy, a teddy bear) mid-disclosure before
  opening up at trust 0.75. A kid dodging, not a model stonewalling.

**Accepted as character texture, not defects** (decision: keep, don't prompt-engineer away):
- Run-to-run mood/length variance (one run terse and withdrawn, another chatty)
  — reads as a living character; TTS carries the mood.
- Occasional kid-plausible slips: "Do you like my dress?" on a voice-only medium,
  a small metaphor ("like a thunderstorm, but there's no lightning"), mum drawn
  harsher in one run than the backstory strictly specifies. In-genre invention,
  strengthens the script rather than breaking it.

**Verdict: llama3.2:3b confirmed. Screening closed.**

Note for integration (tracked in `local-stack/TODO.md`): the harness hardcodes
trust per turn, so even hostile participants "earn" trust on schedule. The real
trust engine must gate trust on participant behavior — separate build item, out
of scope for model screening.
