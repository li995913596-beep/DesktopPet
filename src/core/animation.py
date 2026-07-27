"""AnimationManager – procedural effects + optional frame sequences.

Frame folders (optional):
  assets/pets/<name>/animations/<state>/001.png, 002.png, ...
If present, those frames are played; otherwise procedural motion is used.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QObject, QTimer, Signal, QPoint, Qt
from PySide6.QtGui import QPixmap, QPainter, QColor

from src.core.state_machine import PetState
from src.utils.logger import get_logger
from src.utils.paths import get_pet_dir

logger = get_logger("animation")

# Map PetState → folder name under animations/
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
        self._timer.setInterval(50)
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
        # Advance frame sequence every ~3 ticks (~150ms)
        if self._tick % 3 == 0:
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
        """Livelier single-image motion until real frames exist."""
        if self._base.isNull():
            return QPixmap(), QPoint(0, 0)

        pix = self._base
        offset = QPoint(0, 0)
        t = self._tick

        if self._state == PetState.IDLE:
            # Breathing + tiny sway
            scale_y = 1.0 + 0.02 * math.sin(t * 0.06)
            scale_x = 1.0 + 0.008 * math.sin(t * 0.06 + 0.5)
            new_w = max(1, int(self._base.width() * scale_x))
            new_h = max(1, int(self._base.height() * scale_y))
            pix = self._base.scaled(
                new_w, new_h,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            offset = QPoint(int(2 * math.sin(t * 0.04)), 0)

        elif self._state == PetState.LOOK_AROUND:
            dx = int(10 * math.sin(t * 0.1))
            offset = QPoint(dx, 0)

        elif self._state in (PetState.YAWN, PetState.STRETCH):
            s = 1.0 - 0.06 * abs(math.sin(min(t, 40) * 0.12))
            pix = self._base.scaled(
                max(1, int(self._base.width() * (1.0 + (1.0 - s)))),
                max(1, int(self._base.height() * s)),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        elif self._state == PetState.SLEEP:
            offset = QPoint(0, 5)
            # slight dim could be done later with a darkened copy

        elif self._state in (PetState.CLICK, PetState.HAPPY):
            # Bounce
            phase = min(t, 25)
            dy = -int(12 * abs(math.sin(phase * 0.35)))
            offset = QPoint(0, dy)

        elif self._state == PetState.WALK:
            dx = int(6 * math.sin(t * 0.2))
            dy = int(2 * abs(math.sin(t * 0.4)))  # tiny hop
            offset = QPoint(dx, dy)

        elif self._state == PetState.TALK:
            # Small excited bob
            dy = -int(3 * abs(math.sin(t * 0.25)))
            offset = QPoint(0, dy)

        return pix, offset
