"""Unified animation manager (placeholder for future frame / state machine)."""

from __future__ import annotations

from enum import Enum, auto
from typing import Callable, Optional

from src.utils.logger import get_logger

logger = get_logger("animation")


class AnimationState(Enum):
    """Supported animation states."""

    IDLE = auto()
    CLICK = auto()
    MOVE = auto()
    SLEEP = auto()
    HAPPY = auto()
    SAD = auto()
    ANGRY = auto()


class AnimationManager:
    """Manage pet animation states and transitions.

    Currently a lightweight placeholder. Will support frame sequences
    and state machines in later versions.
    """

    def __init__(self) -> None:
        self._state = AnimationState.IDLE
        self._on_state_changed: Optional[Callable[[AnimationState], None]] = None

    @property
    def state(self) -> AnimationState:
        return self._state

    def set_state(self, state: AnimationState) -> None:
        if state == self._state:
            return
        logger.debug("Animation state: %s -> %s", self._state.name, state.name)
        self._state = state
        if self._on_state_changed:
            self._on_state_changed(state)

    def on_state_changed(self, callback: Callable[[AnimationState], None]) -> None:
        self._on_state_changed = callback

    def play_click(self) -> None:
        self.set_state(AnimationState.CLICK)
        # TODO: play animation then return to IDLE

    def play_idle(self) -> None:
        self.set_state(AnimationState.IDLE)
