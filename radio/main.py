import asyncio
import random
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="MirrorMe: Radio", version="0.1.0-v0")
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------------------------
# Session store
# ---------------------------------------------------------------------------

sessions: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Narrative sequence — v0.1: lock-on radii halved from v0
# ---------------------------------------------------------------------------

NARRATIVE_SEQUENCE = [
    {"step": 0, "type": "intro"},
    {"step": 1, "type": "chapter",     "life_stage": "infancy-tween", "lock_on_radius": 0.25},
    {"step": 2, "type": "listen_only",                                 "lock_on_radius": 0.15},
    {"step": 3, "type": "chapter",     "life_stage": "20s",           "lock_on_radius": 0.20},
    {"step": 4, "type": "chapter",     "life_stage": "30-40s",        "lock_on_radius": 0.15},
    {"step": 5, "type": "listen_only",                                 "lock_on_radius": 0.15},
    {"step": 6, "type": "chapter",     "life_stage": "60s",           "lock_on_radius": 0.10},
    {"step": 7, "type": "chapter",     "life_stage": "80s",           "lock_on_radius": 0.05},
    {"step": 8, "type": "outro"},
]

# Placeholder inner-critic lines per chapter (replaced by live voice pipeline in v1)
CHAPTER_LINES: dict[str, str] = {
    "infancy-tween": "...",
    "20s": "...",
    "30-40s": "...",
    "60s": "...",
    "80s": "...",
}

LISTEN_ONLY_TEXT: dict[int, str] = {
    2: "...",
    5: "...",
}

INTRO_TEXT = "..."

OUTRO_TEXT = "..."

LISTEN_ONLY_DURATION = 3  # seconds (placeholder — no audio yet; replace with clip length in v1)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def pick_frequency(previous: Optional[float]) -> float:
    """Random float in [88.1, 107.9] at least 5 MHz from previous."""
    for _ in range(300):
        freq = round(random.uniform(88.1, 107.9), 1)
        if previous is None or abs(freq - previous) >= 5.0:
            return freq
    return 88.1 if (previous is None or abs(88.1 - previous) >= 5.0) else 107.9


def make_session(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "narrative_sequence": [s.copy() for s in NARRATIVE_SEQUENCE],
        "current_step_index": 0,
        "active_frequency": None,
        "previous_frequency": None,
        "lock_on_radius": 0.25,
        "started": False,
        "locked_on": False,
    }


def current_step(session: dict) -> dict:
    return session["narrative_sequence"][session["current_step_index"]]


def advance_step(session: dict) -> bool:
    """Move to next step and set up frequency if needed. Returns False when exhausted."""
    session["current_step_index"] += 1
    session["locked_on"] = False

    idx = session["current_step_index"]
    if idx >= len(session["narrative_sequence"]):
        return False

    step = session["narrative_sequence"][idx]
    if step["type"] in ("chapter", "listen_only"):
        prev = session["active_frequency"]
        session["previous_frequency"] = prev
        session["active_frequency"] = pick_frequency(prev)
        session["lock_on_radius"] = step["lock_on_radius"]

    return True


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/")
async def root():
    return FileResponse("static/radio.html")


@app.get("/debug/{session_id}")
async def debug_session(session_id: str):
    s = sessions.get(session_id)
    if not s:
        return {"error": "session not found"}
    return s


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@app.websocket("/ws/{session_id}")
async def ws_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()

    # Preserve step progress if client reconnects with the same session_id
    if session_id in sessions:
        session = sessions[session_id]
        session["locked_on"] = False  # old WS is gone; reset lock so client can re-tune
    else:
        session = make_session(session_id)
        sessions[session_id] = session
    listen_task: Optional[asyncio.Task] = None

    # Intro fires immediately on connect — no client action needed
    await websocket.send_json({
        "type": "intro",
        "text": INTRO_TEXT,
        "step": 0,
    })

    try:
        while True:
            data = await websocket.receive_json()
            msg = data.get("type")

            # ----------------------------------------------------------
            # start — client signals the user clicked "Begin" after intro
            # ----------------------------------------------------------
            if msg == "start" and not session["started"]:
                session["started"] = True
                advance_step(session)
                step = current_step(session)
                await websocket.send_json({
                    "type": "frequency_loaded",
                    "active_frequency": session["active_frequency"],
                    "lock_on_radius": step["lock_on_radius"],
                    "step": session["current_step_index"],
                })

            # ----------------------------------------------------------
            # tune — client reports current dial position
            # ----------------------------------------------------------
            elif msg == "tune" and session["started"] and not session["locked_on"]:
                freq = float(data.get("frequency", 0.0))
                step = current_step(session)

                if step["type"] not in ("chapter", "listen_only"):
                    continue

                if abs(freq - session["active_frequency"]) <= session["lock_on_radius"]:
                    session["locked_on"] = True

                    if step["type"] == "chapter":
                        await websocket.send_json({
                            "type": "chapter_start",
                            "life_stage": step["life_stage"],
                            "text": CHAPTER_LINES.get(step["life_stage"], "..."),
                            "lock_on_radius": session["lock_on_radius"],
                            "step": session["current_step_index"],
                        })

                    else:  # listen_only
                        step_idx = session["current_step_index"]
                        await websocket.send_json({
                            "type": "listen_only_start",
                            "indicator": "white_light",
                            "duration_seconds": LISTEN_ONLY_DURATION,
                            "text": LISTEN_ONLY_TEXT.get(step_idx, "..."),
                            "step": step_idx,
                        })

                        async def _listen_timer(ws=websocket, sess=session):
                            await asyncio.sleep(LISTEN_ONLY_DURATION)
                            await ws.send_json({"type": "listen_only_end"})
                            await _advance_and_notify(ws, sess)

                        if listen_task and not listen_task.done():
                            listen_task.cancel()
                        listen_task = asyncio.create_task(_listen_timer())

                else:
                    await websocket.send_json({
                        "type": "frequency_status",
                        "status": "static",
                    })

            # ----------------------------------------------------------
            # chapter_complete — client confirms the chapter is done
            # ----------------------------------------------------------
            elif msg == "chapter_complete" and session["locked_on"]:
                step = current_step(session)
                if step["type"] == "chapter":
                    await _advance_and_notify(websocket, session)

    except WebSocketDisconnect:
        pass
    finally:
        if listen_task and not listen_task.done():
            listen_task.cancel()
        sessions.pop(session_id, None)


# ---------------------------------------------------------------------------
# Shared advance helper
# ---------------------------------------------------------------------------


async def _advance_and_notify(websocket: WebSocket, session: dict) -> None:
    has_more = advance_step(session)

    if not has_more:
        await websocket.send_json({"type": "experience_complete"})
        return

    step = current_step(session)

    if step["type"] == "outro":
        await websocket.send_json({
            "type": "outro",
            "text": OUTRO_TEXT,
            "step": session["current_step_index"],
        })
        await websocket.send_json({"type": "experience_complete"})

    elif step["type"] in ("chapter", "listen_only"):
        await websocket.send_json({
            "type": "frequency_loaded",
            "active_frequency": session["active_frequency"],
            "lock_on_radius": step["lock_on_radius"],
            "step": session["current_step_index"],
        })
