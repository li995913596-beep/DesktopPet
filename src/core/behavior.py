"""BehaviorManager – selects and runs autonomous behaviors."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable, List, Optional

from PySide6.QtCore import QObject, Signal

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
    on_start: Optional[Callable[[], None]] = None


class BehaviorManager(QObject):
    behavior_finished = Signal()
    request_move = Signal(int, int)

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
            Behavior("idle", PetState.IDLE, 32, 2500, 7000),
            Behavior("walk", PetState.WALK, 16, 2000, 4500),
            Behavior("look_around", PetState.LOOK_AROUND, 14, 1800, 3500),
            Behavior("stretch", PetState.STRETCH, 8, 1500, 2800),
            Behavior("yawn", PetState.YAWN, 8, 1500, 2800),
            Behavior("sleep", PetState.SLEEP, 5, 8000, 18000),
            # Higher talk chance so the pet actually speaks
            Behavior("talk", PetState.TALK, 14, 2200, 4000, on_start=self._do_talk),
        ]

    def _do_talk(self) -> None:
        self._bubble.say_random()

    def select_and_start(self) -> int:
        multipliers = self._emotion.behavior_multipliers()
        weights = [
            max(0.01, b.base_weight * multipliers.get(b.name, 1.0))
            for b in self._behaviors
        ]
        chosen = random.choices(self._behaviors, weights=weights, k=1)[0]
        duration = random.randint(chosen.min_duration_ms, chosen.max_duration_ms)
        self._start(chosen)
        return duration

    def force(self, name: str, duration_ms: int = 2000) -> None:
        for b in self._behaviors:
            if b.name == name:
                self._start(b)
                return
        self._sm.set_state(PetState.CLICK)
        self._anim.play(PetState.CLICK)

    def force_click(self) -> int:
        """Click reaction: bounce + speak. Returns duration ms."""
        self._sm.set_state(PetState.CLICK)
        self._anim.play(PetState.CLICK)
        self._bubble.say_random()
        logger.info("Behavior: click reaction")
        return 1800

    def _start(self, behavior: Behavior) -> None:
        self._current = behavior
        self._sm.set_state(behavior.state)
        self._anim.play(behavior.state)
        if behavior.on_start:
            behavior.on_start()
        logger.info("Behavior start: %s", behavior.name)

        if behavior.name == "walk":
            dx = random.choice([-1, 1]) * random.randint(25, 70)
            dy = random.randint(-12, 12)
            self.request_move.emit(dx, dy)

    @property
    def current_name(self) -> str:
        return self._current.name if self._current else "none"
