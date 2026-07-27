"""Pet – aggregate root."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, Signal, QPoint
from PySide6.QtGui import QPixmap

from src.core.config import ConfigManager
from src.core.resource_manager import ResourceManager
from src.core.scheduler import Scheduler
from src.core.emotion import EmotionManager
from src.core.state_machine import StateMachine
from src.core.animation import AnimationManager
from src.core.bubble import BubbleManager
from src.core.behavior import BehaviorManager
from src.core.brain import PetBrain
from src.utils.logger import get_logger

logger = get_logger("pet")


class Pet(QObject):
    frame_changed = Signal(QPixmap, QPoint)
    bubble_show = Signal(str, int)
    bubble_hide = Signal()
    request_move = Signal(int, int)

    def __init__(self, config: ConfigManager, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self.config = config
        self.resources = ResourceManager()

        self.scheduler = Scheduler(self)
        self.emotion = EmotionManager()
        self.state_machine = StateMachine()
        self.animation = AnimationManager(self)
        self.bubble = BubbleManager(self.emotion, self)
        self.behavior = BehaviorManager(
            self.state_machine, self.animation, self.emotion, self.bubble, self
        )
        self.brain = PetBrain(
            self.scheduler, self.emotion, self.behavior,
            self.state_machine, self.animation, self.bubble, self
        )

        self.animation.frame_changed.connect(self.frame_changed)
        self.bubble.show_text.connect(self.bubble_show)
        self.bubble.hide.connect(self.bubble_hide)
        self.behavior.request_move.connect(self.request_move)

        self._load_appearance()

    def _load_appearance(self) -> None:
        name = self.config.settings.pet_name
        self.animation.set_pet_name(name)
        pix = self.resources.get_pet_image(name)
        if pix is None or pix.isNull():
            logger.warning("No pet image for %s", name)
            return
        self.animation.set_base_pixmap(pix)
        self.animation.play(self.state_machine.state)

    def handle_click(self) -> None:
        self.brain.on_user_click()

    def handle_drag(self) -> None:
        self.brain.on_user_drag()

    def shutdown(self) -> None:
        self.scheduler.cancel_all()
        self.animation.stop()
