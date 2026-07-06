"""Quick voice test — run with: python3 -m llm.test_voice [--model ollama-model-name]"""
import sys
import time
import urllib.request
import json

MODEL = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "llama3.2:3b"
SYSTEM_PROMPT = open("llm/system_prompt.txt").read()

# A scripted conversation. trust_level simulates empathy building over time.
# Edit these lines freely to test different participant approaches.
CONVERSATION = [
    {"participant": "Hi... is someone there?",                          "trust": 0.0},
    {"participant": "What's your name?",                                "trust": 0.1},
    {"participant": "That's a nice name. How old are you?",             "trust": 0.2},
    {"participant": "Are you okay? You sound a little sad.",            "trust": 0.3},
    {"participant": "I hear you. That sounds really hard.",             "trust": 0.45},
    {"participant": "Do you want to tell me what the voices sound like?","trust": 0.6},
    {"participant": "You don't have to be scared. I'm not going anywhere.","trust": 0.75},
]


def ask(messages: list, trust_level: float) -> tuple[str, float]:
    system = SYSTEM_PROMPT.replace("{trust_level}", str(trust_level))
    payload = json.dumps({
        "model": MODEL,
        "system": system,
        "messages": messages,
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
    print(f"Model: {MODEL}")
    history = []
    print(f"{'─'*60}")
    for turn in CONVERSATION:
        participant_text = turn["participant"]
        trust = turn["trust"]

        history.append({"role": "user", "content": participant_text})
        response, ms = ask(history, trust)
        history.append({"role": "assistant", "content": response})

        print(f"\nPARTICIPANT: {participant_text}")
        print(f"CHARACTER (trust={trust}, {ms:.0f}ms): {response}")
        print(f"{'─'*60}")
