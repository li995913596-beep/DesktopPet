"""AnimationManager – owns visual presentation of the current state.

Until multi-frame assets exist, uses lightweight procedural effects
(breath, look offset, squash, dim) so the pet already feels alive.
Later this will load assets/pets/<name>/animations/<state>/*.png.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal, QPoint
from PySide6.QtGui import QPixmap, QTransform

from src.core.state_machine import PetState
from src.utils.logger import get_logger

logger = get_logger("animation")


class AnimationManager(QObject):
    """Produces the pixmap that the Renderer should draw each frame."""

    # Emitted whenever the displayed pixmap or preferred offset changes
    frame_changed = Signal(QPixmap, QPoint)  # pixmap, local offset

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._base: QPixmap = QPixmap()
        self._state = PetState.IDLE
        self._tick = 0
        self._offset = QPoint(0, 0)

        self._timer = QTimer(self)
        self._timer.setInterval(50)  # 20 fps procedural
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
            # Gentle breathing: tiny vertical scale pulse
            import math
            scale_y = 1.0 + 0.012 * math.sin(t * 0.08)
            h = max(1, int(pix.height() * scale_y))
            pix = pix.scaled(pix.width(), h, mode=pix.scaled(pix.size()).TransformationMode.SmoothTransformation
                             if False else __import__("PySide6.QtCore", fromlist=["Qt"]).Qt.TransformationMode.SmoothTransformation)
            # simpler approach without import mess:
            from PySide6.QtCore import Qt
            pix = self._base.scaled(
                self._base.width(),
                max(1, int(self._base.height() * scale_y)),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        elif self._state == PetState.LOOK_AROUND:
            # Shift left/right
            import math
            dx = int(6 * math.sin(t * 0.12))
            offset = QPoint(dx, 0)

        elif self._state == PetState.YAWN or self._state == PetState.STRETCH:
            # Slight squash
            from PySide6.QtCore import Qt
            import math
            s = 1.0 - 0.04 * abs(math.sin(t * 0.15))
            pix = self._base.scaled(
                max(1, int(self._base.width() * (2 - s))),
                max(1, int(self._base.height() * s)),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        elif self._state == PetState.SLEEP:
            # Dim + slight downward settle
            from PySide6.QtCore import Qt
            pix = self._base
            offset = QPoint(0, 3)

        elif self._state == PetState.CLICK or self._state == PetState.HAPPY:
            # Quick bounce
            import math
            dy = -int(8 * abs(math.sin(t * 0.35)))
            offset = QPoint(0, dy)

        elif self._state == PetState.WALK:
            import math
            dx = int(4 * math.sin(t * 0.2))
            offset = QPoint(dx, 0)

        self._offset = offset
        self.frame_changed.emit(pix, offset)
