"""Lightweight finite state machine for pet activity."""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Optional

from src.utils.logger import get_logger

logger = get_logger("state_machine")


class PetState(Enum):
    """High-level activity states."""

    IDLE = auto()
    WALK = auto()
    LOOK_AROUND = auto()
    STRETCH = auto()
    YAWN = auto()
    SLEEP = auto()
    CLICK = auto()
    FOLLOW_MOUSE = auto()
    TALK = auto()
    HAPPY = auto()


class StateMachine:
    """Simple FSM. Behaviors set the state; AnimationManager reacts to it."""

    def __init__(self) -> None:
        self._state = PetState.IDLE
        self._on_changed: Optional[Callable[[PetState, PetState], None]] = None

    @property
    def state(self) -> PetState:
        return self._state

    def set_state(self, new_state: PetState) -> None:
        if new_state == self._state:
            return
        old = self._state
        self._state = new_state
        logger.debug("State: %s -> %s", old.name, new_state.name)
        if self._on_changed:
            self._on_changed(old, new_state)

    def on_state_changed(self, callback: Callable[[PetState, PetState], None]) -> None:
        self._on_changed = callback
