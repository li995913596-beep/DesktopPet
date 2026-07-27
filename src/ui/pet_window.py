"""Transparent, frameless, always-on-top pet window with perfect alpha support."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import (
    QPixmap,
    QMouseEvent,
    QWheelEvent,
    QPainter,
    QPaintEvent,
    QCloseEvent,
)
from PySide6.QtWidgets import QWidget

from src.core.config import ConfigManager
from src.core.resource_manager import ResourceManager
from src.utils.logger import get_logger

logger = get_logger("pet_window")

# Product-required scale steps (80% ~ 200%)
SCALE_STEPS: list[float] = [0.8, 0.9, 1.0, 1.2, 1.5, 2.0]

# Target default display height in pixels (comfortable desktop size)
DEFAULT_TARGET_HEIGHT: int = 200


class PetWindow(QWidget):
    """Main desktop pet window.

    Design goals:
    - True per-pixel transparency (no white/black/gray rectangle)
    - Always on top, never steals focus
    - Left-drag move, wheel scale (persisted)
    - Close event hides to tray (does not quit)
    """

    quit_requested = Signal()

    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self.config = config
        self.resources = ResourceManager()
        self._drag_pos: QPoint | None = None
        self._scale: float = float(config.settings.scale)
        self._original_pixmap = QPixmap()
        self._scaled_pixmap = QPixmap()

        self._setup_window_flags()
        self._load_pet_image()
        self._restore_geometry()

    def _setup_window_flags(self) -> None:
        """Frameless + translucent + always-on-top + no focus steal."""
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)

    def _load_pet_image(self) -> None:
        pet_name = self.config.settings.pet_name
        pixmap = self.resources.get_pet_image(pet_name)

        if pixmap is None or pixmap.isNull():
            pixmap = QPixmap(160, 160)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            painter.setPen(Qt.GlobalColor.magenta)
            painter.drawRect(4, 4, 151, 151)
            painter.drawText(
                pixmap.rect(),
                Qt.AlignmentFlag.AlignCenter,
                "No Image\n(add pet.png)",
            )
            painter.end()
            logger.warning(
                "Pet image missing for '%s'. Place transparent PNG at "
                "assets/pets/%s/pet.png",
                pet_name,
                pet_name,
            )

        self._original_pixmap = pixmap

        # Auto-fit to comfortable size if current scale would make it too large
        # or if this is effectively first run (scale == 1.0)
        current_h = pixmap.height() * self._scale
        if current_h > DEFAULT_TARGET_HEIGHT * 1.15 or abs(self._scale - 1.0) < 1e-6:
            auto_scale = DEFAULT_TARGET_HEIGHT / float(pixmap.height())
            self._scale = min(SCALE_STEPS, key=lambda s: abs(s - auto_scale))
            self.config.set("scale", self._scale)
            logger.info(
                "Auto-scaled to %.0f%% (target height ~%dpx)",
                self._scale * 100,
                DEFAULT_TARGET_HEIGHT,
            )

        self._apply_scale()

    def _apply_scale(self) -> None:
        if self._original_pixmap.isNull():
            return

        target = self._original_pixmap.size() * self._scale
        self._scaled_pixmap = self._original_pixmap.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        size = self._scaled_pixmap.size()
        self.resize(size)
        self.setFixedSize(size)
        self.update()

    def _restore_geometry(self) -> None:
        s = self.config.settings
        self.move(int(s.pos_x), int(s.pos_y))

    def paintEvent(self, event: QPaintEvent) -> None:
        if self._scaled_pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.drawPixmap(0, 0, self._scaled_pixmap)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self._drag_pos = None
            pos = self.pos()
            self.config.set("pos_x", pos.x())
            self.config.set("pos_y", pos.y())
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        if delta == 0:
            return

        try:
            idx = SCALE_STEPS.index(self._scale)
        except ValueError:
            idx = min(
                range(len(SCALE_STEPS)),
                key=lambda i: abs(SCALE_STEPS[i] - self._scale),
            )

        if delta > 0:
            idx = min(idx + 1, len(SCALE_STEPS) - 1)
        else:
            idx = max(idx - 1, 0)

        self._scale = SCALE_STEPS[idx]
        self._apply_scale()
        self.config.set("scale", self._scale)
        logger.debug("Scale set to %.0f%%", self._scale * 100)
        event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
        logger.info("Pet window hidden to tray.")

    def show_pet(self) -> None:
        self.show()
        self.raise_()

    def set_always_on_top(self, enabled: bool) -> None:
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()
        self.config.set("always_on_top", enabled)
