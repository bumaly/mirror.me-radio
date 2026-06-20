"""
Session state schema for MirrorMe: Radio v0.

In-memory only — no database. One dict per connected WebSocket client,
keyed by session_id in main.py's `sessions` store.
"""

from typing import Optional
from pydantic import BaseModel


class StepDefinition(BaseModel):
    step: int
    type: str                          # intro | chapter | listen_only | outro
    life_stage: Optional[str] = None   # infancy-tween | 20s | 30-40s | 60s | 80s
    lock_on_radius: Optional[float] = None


class SessionState(BaseModel):
    """Canonical shape of the session dict stored in main.py."""
    session_id: str
    narrative_sequence: list[StepDefinition]
    current_step_index: int = 0
    active_frequency: Optional[float] = None    # the one hot freq on the dial
    previous_frequency: Optional[float] = None  # for ≥5 MHz spacing constraint
    lock_on_radius: float = 0.5                 # narrows as chapters progress
    started: bool = False                        # True after client sends "start"
    locked_on: bool = False                      # True while a step is active

    class Config:
        # Allow extra fields (e.g. asyncio task refs stored alongside in main.py)
        extra = "allow"
