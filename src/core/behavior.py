"""BehaviorManager – selects and runs autonomous behaviors."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from PySide6.QtCore import QObject, QPoint, Signal

from src.core.emotion import EmotionManager
from src.core.state_machine import PetState, StateMachine
from src.core.animation import AnimationManager
from src.core.bubble import BubbleManager
from src.utils.logger import get_logger

logger = get_logger("behavior")


@dataclass
class Behavior:
    name: str
    state: PetState
    base_weight: float
    min_duration_ms: int
    max_duration_ms: int
    # Optional side-effect when behavior starts
    on_start: Optional[Callable[[], None]] = None


class BehaviorManager(QObject):
    """Owns the catalog of behaviors and the currently running one.

    Weights are multiplied by EmotionManager multipliers so mood
    actually changes what the pet prefers to do.
    """

    behavior_finished = Signal()
    # Request the renderer / pet to move by delta (for walk)
    request_move = Signal(int, int)  # dx, dy

    def __init__(
        self,
        state_machine: StateMachine,
        animation: AnimationManager,
        emotion: EmotionManager,
        bubble: BubbleManager,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._sm = state_machine
        self._anim = animation
        self._emotion = emotion
        self._bubble = bubble
        self._current: Optional[Behavior] = None
        self._behaviors: List[Behavior] = []
        self._build_catalog()

    def _build_catalog(self) -> None:
        self._behaviors = [
            Behavior("idle", PetState.IDLE, 40, 3000, 8000),
            Behavior("walk", PetState.WALK, 18, 2000, 5000),
            Behavior("look_around", PetState.LOOK_AROUND, 12, 2000, 4000),
            Behavior("stretch", PetState.STRETCH, 8, 1500, 3000),
            Behavior("yawn", PetState.YAWN, 8, 1500, 3000),
            Behavior("sleep", PetState.SLEEP, 6, 8000, 20000),
            Behavior("talk", PetState.TALK, 8, 2000, 4000, on_start=self._do_talk),
        ]

    def _do_talk(self) -> None:
        self._bubble.say_random()

    def select_and_start(self) -> int:
        """Pick a behavior by weighted random and start it.

        Returns suggested duration in ms so the caller can schedule finish.
        """
        multipliers = self._emotion.behavior_multipliers()
        weights = []
        for b in self._behaviors:
            w = b.base_weight * multipliers.get(b.name, 1.0)
            weights.append(max(0.01, w))

        chosen = random.choices(self._behaviors, weights=weights, k=1)[0]
        duration = random.randint(chosen.min_duration_ms, chosen.max_duration_ms)
        self._start(chosen)
        return duration

    def force(self, name: str, duration_ms: int = 2000) -> None:
        """Force a named behavior (e.g. click reaction)."""
        for b in self._behaviors:
            if b.name == name:
                self._start(b)
                return
        # fallback click
        self._sm.set_state(PetState.CLICK)
        self._anim.play(PetState.CLICK)

    def _start(self, behavior: Behavior) -> None:
        self._current = behavior
        self._sm.set_state(behavior.state)
        self._anim.play(behavior.state)
        if behavior.on_start:
            behavior.on_start()
        logger.info("Behavior start: %s", behavior.name)

        if behavior.name == "walk":
            # Small random step; Renderer will apply
            dx = random.choice([-1, 1]) * random.randint(20, 60)
            dy = random.randint(-15, 15)
            self.request_move.emit(dx, dy)

    @property
    def current_name(self) -> str:
        return self._current.name if self._current else "none"
