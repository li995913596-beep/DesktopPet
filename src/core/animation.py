"""AnimationManager – owns visual presentation of the current state.

Until multi-frame assets exist, uses lightweight procedural effects
(breath, look offset, squash) so the pet already feels alive.
Later this will load assets/pets/<name>/animations/<state>/*.png.
"""

from __future__ import annotations

import math
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, QPoint, Qt
from PySide6.QtGui import QPixmap

from src.core.state_machine import PetState
from src.utils.logger import get_logger

logger = get_logger("animation")


class AnimationManager(QObject):
    """Produces the pixmap that the Renderer should draw each frame."""

    frame_changed = Signal(QPixmap, QPoint)  # pixmap, local offset

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._base: QPixmap = QPixmap()
        self._state = PetState.IDLE
        self._tick = 0
        self._offset = QPoint(0, 0)

        self._timer = QTimer(self)
        self._timer.setInterval(50)  # ~20 fps procedural
        self._timer.timeout.connect(self._on_tick)

    def set_base_pixmap(self, pixmap: QPixmap) -> None:
        self._base = pixmap
        self._emit_current()

    def play(self, state: PetState) -> None:
        self._state = state
        self._tick = 0
        self._offset = QPoint(0, 0)
        if not self._timer.isActive():
            self._timer.start()
        self._emit_current()
        logger.debug("Animation play: %s", state.name)

    def stop(self) -> None:
        self._timer.stop()
        self._offset = QPoint(0, 0)
        self._emit_current()

    def _on_tick(self) -> None:
        self._tick += 1
        self._emit_current()

    def _emit_current(self) -> None:
        if self._base.isNull():
            return

        pix = self._base
        offset = QPoint(0, 0)
        t = self._tick

        if self._state == PetState.IDLE:
            # Gentle breathing
            scale_y = 1.0 + 0.015 * math.sin(t * 0.07)
            new_h = max(1, int(self._base.height() * scale_y))
            pix = self._base.scaled(
                self._base.width(),
                new_h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        elif self._state == PetState.LOOK_AROUND:
            dx = int(7 * math.sin(t * 0.11))
            offset = QPoint(dx, 0)

        elif self._state in (PetState.YAWN, PetState.STRETCH):
            s = 1.0 - 0.05 * abs(math.sin(t * 0.14))
            pix = self._base.scaled(
                max(1, int(self._base.width() * (1.0 + (1.0 - s) * 0.5))),
                max(1, int(self._base.height() * s)),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        elif self._state == PetState.SLEEP:
            offset = QPoint(0, 4)

        elif self._state in (PetState.CLICK, PetState.HAPPY):
            dy = -int(10 * abs(math.sin(min(t, 20) * 0.4)))
            offset = QPoint(0, dy)

        elif self._state == PetState.WALK:
            dx = int(5 * math.sin(t * 0.18))
            offset = QPoint(dx, 0)

        self._offset = offset
        self.frame_changed.emit(pix, offset)
