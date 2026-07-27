"""AnimationManager – smoother procedural motion + optional frame sequences."""

from __future__ import annotations

import math
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal, QPoint, Qt
from PySide6.QtGui import QPixmap

from src.core.state_machine import PetState
from src.utils.logger import get_logger
from src.utils.paths import get_pet_dir

logger = get_logger("animation")

STATE_FOLDER: Dict[PetState, str] = {
    PetState.IDLE: "idle",
    PetState.WALK: "walk",
    PetState.LOOK_AROUND: "look",
    PetState.STRETCH: "stretch",
    PetState.YAWN: "yawn",
    PetState.SLEEP: "sleep",
    PetState.CLICK: "click",
    PetState.HAPPY: "happy",
    PetState.TALK: "talk",
    PetState.FOLLOW_MOUSE: "idle",
}


class AnimationManager(QObject):
    frame_changed = Signal(QPixmap, QPoint)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._base: QPixmap = QPixmap()
        self._state = PetState.IDLE
        self._tick = 0
        self._offset = QPoint(0, 0)
        self._pet_name = "Girl"
        self._frame_sets: Dict[str, List[QPixmap]] = {}
        self._frame_index = 0

        self._timer = QTimer(self)
        self._timer.setInterval(40)  # slightly smoother
        self._timer.timeout.connect(self._on_tick)

    def set_pet_name(self, name: str) -> None:
        self._pet_name = name
        self._frame_sets.clear()
        self._load_all_frame_sets()

    def set_base_pixmap(self, pixmap: QPixmap) -> None:
        self._base = pixmap
        self._emit_current()

    def _load_all_frame_sets(self) -> None:
        anim_root = get_pet_dir(self._pet_name) / "animations"
        if not anim_root.is_dir():
            return
        for folder in anim_root.iterdir():
            if not folder.is_dir():
                continue
            frames: List[QPixmap] = []
            for f in sorted(folder.glob("*.png")):
                pix = QPixmap(str(f))
                if not pix.isNull():
                    frames.append(pix)
            if frames:
                self._frame_sets[folder.name] = frames
                logger.info("Loaded %d frames for '%s'", len(frames), folder.name)

    def play(self, state: PetState) -> None:
        self._state = state
        self._tick = 0
        self._frame_index = 0
        self._offset = QPoint(0, 0)
        if not self._timer.isActive():
            self._timer.start()
        self._emit_current()

    def stop(self) -> None:
        self._timer.stop()
        self._offset = QPoint(0, 0)
        self._emit_current()

    def _on_tick(self) -> None:
        self._tick += 1
        if self._tick % 4 == 0:
            folder = STATE_FOLDER.get(self._state, "")
            frames = self._frame_sets.get(folder)
            if frames:
                self._frame_index = (self._frame_index + 1) % len(frames)
        self._emit_current()

    def _emit_current(self) -> None:
        if self._base.isNull() and not self._frame_sets:
            return

        folder = STATE_FOLDER.get(self._state, "")
        frames = self._frame_sets.get(folder)

        if frames:
            pix = frames[self._frame_index % len(frames)]
            offset = QPoint(0, 0)
        else:
            pix, offset = self._procedural()

        self._offset = offset
        self.frame_changed.emit(pix, offset)

    def _procedural(self) -> tuple[QPixmap, QPoint]:
        """Softer, less robotic single-image motion."""
        if self._base.isNull():
            return QPixmap(), QPoint(0, 0)

        pix = self._base
        offset = QPoint(0, 0)
        t = self._tick

        if self._state == PetState.IDLE:
            # Very gentle breath + tiny sway (slow sine)
            breath = 1.0 + 0.012 * math.sin(t * 0.045)
            sway = int(1.5 * math.sin(t * 0.03))
            new_h = max(1, int(self._base.height() * breath))
            pix = self._base.scaled(
                self._base.width(),
                new_h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            offset = QPoint(sway, 0)

        elif self._state == PetState.LOOK_AROUND:
            # Smooth look left-right
            dx = int(6 * math.sin(t * 0.07))
            offset = QPoint(dx, 0)

        elif self._state in (PetState.YAWN, PetState.STRETCH):
            # Soft squash, ease in-out feel
            phase = min(t, 50) / 50.0
            s = 1.0 - 0.04 * math.sin(phase * math.pi)
            pix = self._base.scaled(
                max(1, int(self._base.width() * (1.0 + (1.0 - s) * 0.4))),
                max(1, int(self._base.height() * s)),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        elif self._state == PetState.SLEEP:
            offset = QPoint(0, 3)

        elif self._state in (PetState.CLICK, PetState.HAPPY):
            # Quick soft bounce then settle
            phase = min(t, 30)
            dy = -int(8 * abs(math.sin(phase * 0.28)) * (1.0 - phase / 35.0))
            offset = QPoint(0, dy)

        elif self._state == PetState.WALK:
            dx = int(4 * math.sin(t * 0.14))
            dy = int(1.5 * abs(math.sin(t * 0.28)))
            offset = QPoint(dx, dy)

        elif self._state == PetState.TALK:
            dy = -int(2 * abs(math.sin(t * 0.2)))
            offset = QPoint(0, dy)

        return pix, offset
