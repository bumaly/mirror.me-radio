# LLM Decision — 2026-07-06 (in progress)

**Goal: find a local model that holds a fictional child character persona without breaking into AI assistant mode**

The character is a 5-year-old with a specific backstory, emotional arc, and trust-based response system. The model must stay in character across a full conversation — never identifying as an AI, never offering help as an assistant.

---

## Round 1: llama3.2:3b (via ollama)

**Result: DISQUALIFIED — breaks character immediately**

Broke on first turn ("How can I assist you today?") and by turn 2 was explaining that it is "a language model trained on a massive dataset." Explicit system prompt instructions including `IMPORTANT: You are not an AI` had no effect.

**Why this happens:** RLHF (Reinforcement Learning from Human Feedback) trains instruction models to refuse impersonating humans. This is a safety behavior baked into the weights — it cannot be overridden through the system prompt alone. This is a known limitation of heavily instruction-tuned models, not a prompt engineering failure.

| Model | Character held? | Notes |
|-------|----------------|-------|
| llama3.2:3b | ✗ | Breaks on turn 1; RLHF override |

---

## Round 2: In progress

Testing roleplay-fine-tuned models which remove or reduce RLHF restrictions:
- dolphin-mistral (Mistral 7B, Cognitive Computations fine-tune)
- nous-hermes2
- mistral (base)

Results to be added as testing continues.
