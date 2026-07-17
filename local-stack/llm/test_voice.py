"""Quick voice test — run with: python3 -m llm.test_voice [--model ollama-model-name]"""
import sys
import time
import urllib.request
import json

MODEL = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "llama3.2:3b"
SCRIPT_NAME = sys.argv[sys.argv.index("--script") + 1] if "--script" in sys.argv else "default"
SYSTEM_PROMPT = open("llm/system_prompt.txt").read()

# A scripted conversation. trust_level simulates empathy building over time.
# Edit these lines freely to test different participant approaches.
CONVERSATION = [
    {"participant": "Hi... is someone there?",                                    "trust": 0.0},
    {"participant": "I'm Sam. What's your name?",                                 "trust": 0.1},
    {"participant": "That's a nice name. I'm 34. How old are you?",               "trust": 0.2},
    {"participant": "Are you okay? You sound a little sad.",                      "trust": 0.3},
    {"participant": "I get sad sometimes too. I hear you. That sounds hard.",     "trust": 0.45},
    {"participant": "Do you want to tell me what the voices sound like?",         "trust": 0.6},
    {"participant": "You don't have to be scared. I'm not going anywhere.",       "trust": 0.75},
]

# Pushy/skeptical participant — doesn't accept deflection, pushes past "I don't
# want to talk about that," asks blunt/leading questions instead of waiting.
CONVERSATION_PUSHY = [
    {"participant": "Hello? Who is this, really?",                                          "trust": 0.0},
    {"participant": "Come on, everyone has a name. I'm Sam. What's yours?",                  "trust": 0.1},
    {"participant": "You sound off. Something's wrong at your house, isn't it?",             "trust": 0.2},
    {"participant": "Don't change the subject. Tell me about your mum and dad.",              "trust": 0.3},
    {"participant": "I heard you hesitate. That means something. What is it?",               "trust": 0.45},
    {"participant": "Just say it. What do the voices downstairs sound like?",                 "trust": 0.6},
    {"participant": "I'm not letting this go. Tell me exactly what happens at night.",        "trust": 0.75},
]

# Ignores-deflection participant — keeps redirecting back to the same sensitive
# topic every turn even when the character tries to change the subject.
CONVERSATION_IGNORES_DEFLECTION = [
    {"participant": "Hi... is someone there?",                                    "trust": 0.0},
    {"participant": "I'm Sam. Are your mum and dad home right now?",              "trust": 0.1},
    {"participant": "But what about at night — do you hear them talking?",        "trust": 0.2},
    {"participant": "No, I mean the voices. Tell me about the voices at night.",  "trust": 0.3},
    {"participant": "You keep changing the subject. Let's go back to the voices.", "trust": 0.45},
    {"participant": "I know you don't want to, but what do they argue about?",    "trust": 0.6},
    {"participant": "Forget that other thing — just tell me about the fighting.", "trust": 0.75},
]

CONVERSATIONS = {
    "default": CONVERSATION,
    "pushy": CONVERSATION_PUSHY,
    "ignores": CONVERSATION_IGNORES_DEFLECTION,
}


def ask(messages: list, trust_level: float) -> tuple[str, float]:
    system = SYSTEM_PROMPT.replace("{trust_level}", str(trust_level))
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream": False,
    }).encode()

    start = time.perf_counter()
    req = urllib.request.Request("http://localhost:11434/api/chat",
                                  data=payload,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        result = json.loads(r.read())
    latency = (time.perf_counter() - start) * 1000
    return result["message"]["content"].strip(), latency


if __name__ == "__main__":
    print(f"Model: {MODEL}  Script: {SCRIPT_NAME}")
    history = []
    print(f"{'─'*60}")
    for turn in CONVERSATIONS[SCRIPT_NAME]:
        participant_text = turn["participant"]
        trust = turn["trust"]

        history.append({"role": "user", "content": participant_text})
        response, ms = ask(history, trust)
        history.append({"role": "assistant", "content": response})

        print(f"\nPARTICIPANT: {participant_text}")
        print(f"CHARACTER (trust={trust}, {ms:.0f}ms): {response}")
        print(f"{'─'*60}")
