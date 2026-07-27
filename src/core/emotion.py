"""Emotion system. Mood influences behavior weights and speech."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict

from src.utils.logger import get_logger

logger = get_logger("emotion")


class Emotion(Enum):
    HAPPY = auto()
    SLEEPY = auto()
    BORED = auto()
    EXCITED = auto()
    NEUTRAL = auto()


@dataclass
class EmotionState:
    current: Emotion = Emotion.NEUTRAL
    # 0.0 ~ 1.0 intensity
    intensity: float = 0.5


class EmotionManager:
    """Tracks and slowly drifts the pet's mood.

    Future: hunger / energy / weather / AI will modify this.
    """

    def __init__(self) -> None:
        self._state = EmotionState()

    @property
    def current(self) -> Emotion:
        return self._state.current

    @property
    def intensity(self) -> float:
        return self._state.intensity

    def set_emotion(self, emotion: Emotion, intensity: float = 0.6) -> None:
        self._state.current = emotion
        self._state.intensity = max(0.0, min(1.0, intensity))
        logger.debug("Emotion -> %s (%.2f)", emotion.name, intensity)

    def drift_toward_neutral(self, amount: float = 0.02) -> None:
        """Called periodically so strong moods fade."""
        if self._state.current == Emotion.NEUTRAL:
            return
        self._state.intensity = max(0.0, self._state.intensity - amount)
        if self._state.intensity < 0.15:
            self._state.current = Emotion.NEUTRAL
            self._state.intensity = 0.5

    def behavior_multipliers(self) -> Dict[str, float]:
        """Return weight multipliers for named behaviors."""
        e = self._state.current
        base = {
            "idle": 1.0,
            "walk": 1.0,
            "look_around": 1.0,
            "stretch": 1.0,
            "yawn": 1.0,
            "sleep": 1.0,
            "talk": 1.0,
            "follow_mouse": 0.3,
        }
        if e == Emotion.SLEEPY:
            base["sleep"] = 2.5
            base["yawn"] = 2.2
            base["walk"] = 0.4
            base["talk"] = 0.5
        elif e == Emotion.HAPPY:
            base["walk"] = 1.6
            base["talk"] = 1.8
            base["stretch"] = 1.4
            base["sleep"] = 0.3
        elif e == Emotion.BORED:
            base["look_around"] = 1.8
            base["walk"] = 1.5
            base["talk"] = 1.3
        elif e == Emotion.EXCITED:
            base["walk"] = 2.0
            base["follow_mouse"] = 1.5
            base["talk"] = 1.5
            base["sleep"] = 0.2
        return base
