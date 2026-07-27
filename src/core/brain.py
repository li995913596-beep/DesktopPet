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
    """High-level autonomy.

    Scheduler ticks drive 'think' cycles. Emotion drifts over time.
    Long idle without interaction makes the pet sleepy / bored.
    User interaction wakes it up and can force reactions.
    """

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

        # Main think loop – every 4s decide whether to pick a new behavior
        self._scheduler.every("think", 4000, self._think)
        # Emotion drift + idle tracking
        self._scheduler.every("mood", 10000, self._mood_tick)

        # Start with a gentle idle
        self._start_behavior_cycle()

    def _think(self) -> None:
        if self._busy:
            return
        # Occasionally start a new behavior even if one is running
        # (simple model; later behaviors will signal finished)
        self._start_behavior_cycle()

    def _start_behavior_cycle(self) -> None:
        self._busy = True
        duration = self._behavior.select_and_start()
        self._scheduler.once("behavior_end", duration, self._on_behavior_end)

    def _on_behavior_end(self) -> None:
        self._busy = False
        # Return to soft idle animation while waiting for next think
        self._sm.set_state(PetState.IDLE)
        self._anim.play(PetState.IDLE)

    def _mood_tick(self) -> None:
        self._idle_seconds += 10
        self._emotion.drift_toward_neutral(0.03)

        # Long no-interaction → sleepy / bored
        if self._idle_seconds > 180:  # 3 min
            self._emotion.set_emotion(Emotion.SLEEPY, 0.7)
        elif self._idle_seconds > 90:
            self._emotion.set_emotion(Emotion.BORED, 0.5)

    # ----- external stimuli from UI -----

    def on_user_click(self) -> None:
        self._idle_seconds = 0
        self._emotion.set_emotion(Emotion.HAPPY, 0.6)
        self._scheduler.cancel("behavior_end")
        self._behavior.force("idle")  # will be replaced by click anim
        self._sm.set_state(PetState.CLICK)
        self._anim.play(PetState.CLICK)
        self._bubble.say_random()
        self._busy = True
        self._scheduler.once("behavior_end", 1800, self._on_behavior_end)

    def on_user_drag(self) -> None:
        self._idle_seconds = 0

    def on_mouse_nearby(self, global_pos: QPoint) -> None:
        """Optional future: follow / look at mouse."""
        pass
