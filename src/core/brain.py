"""PetBrain – the decision maker that makes the pet feel alive."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QPoint

from src.core.scheduler import Scheduler
from src.core.emotion import EmotionManager, Emotion
from src.core.behavior import BehaviorManager
from src.core.state_machine import StateMachine, PetState
from src.core.animation import AnimationManager
from src.core.bubble import BubbleManager
from src.utils.logger import get_logger

logger = get_logger("brain")


class PetBrain(QObject):
    def __init__(
        self,
        scheduler: Scheduler,
        emotion: EmotionManager,
        behavior: BehaviorManager,
        state_machine: StateMachine,
        animation: AnimationManager,
        bubble: BubbleManager,
        parent: Optional[QObject] = None,
    ) -> None:
        super().__init__(parent)
        self._scheduler = scheduler
        self._emotion = emotion
        self._behavior = behavior
        self._sm = state_machine
        self._anim = animation
        self._bubble = bubble

        self._idle_seconds = 0
        self._busy = False

        self._scheduler.every("think", 3500, self._think)
        self._scheduler.every("mood", 10000, self._mood_tick)

        self._start_behavior_cycle()

    def _think(self) -> None:
        if self._busy:
            return
        self._start_behavior_cycle()

    def _start_behavior_cycle(self) -> None:
        self._busy = True
        duration = self._behavior.select_and_start()
        self._scheduler.once("behavior_end", duration, self._on_behavior_end)

    def _on_behavior_end(self) -> None:
        self._busy = False
        self._sm.set_state(PetState.IDLE)
        self._anim.play(PetState.IDLE)

    def _mood_tick(self) -> None:
        self._idle_seconds += 10
        self._emotion.drift_toward_neutral(0.03)
        if self._idle_seconds > 180:
            self._emotion.set_emotion(Emotion.SLEEPY, 0.7)
        elif self._idle_seconds > 90:
            self._emotion.set_emotion(Emotion.BORED, 0.5)

    def on_user_click(self) -> None:
        self._idle_seconds = 0
        self._emotion.set_emotion(Emotion.HAPPY, 0.65)
        self._scheduler.cancel("behavior_end")
        duration = self._behavior.force_click()
        self._busy = True
        self._scheduler.once("behavior_end", duration, self._on_behavior_end)

    def on_user_drag(self) -> None:
        self._idle_seconds = 0

    def on_mouse_nearby(self, global_pos: QPoint) -> None:
        pass
