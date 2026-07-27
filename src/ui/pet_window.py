"""Transparent, frameless, always-on-top pet window."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QPixmap, QMouseEvent, QWheelEvent, QPainter
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from src.core.config import ConfigManager
from src.core.resource_manager import ResourceManager
from src.utils.logger import get_logger

logger = get_logger("pet_window")

# Allowed scale steps (must match product requirements)
SCALE_STEPS: list[float] = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 1.8, 2.0]


class PetWindow(QWidget):
    """Main desktop pet window.

    Features (current):
    - Frameless + transparent background
    - Always on top, does not steal focus
    - Left-button drag (position persisted)
    - Mouse-wheel scale with nice steps (scale persisted)
    """

    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self.config = config
        self.resources = ResourceManager()
        self._drag_pos: QPoint | None = None
        self._scale: float = float(config.settings.scale)
        self._original_pixmap = QPixmap()

        self._setup_window_flags()
        self._setup_ui()
        self._load_pet_image()
        self._restore_geometry()

    def _setup_window_flags(self) -> None:
        """Configure frameless, transparent, always-on-top, no-focus window."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # avoids taskbar entry & focus stealing on Windows
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        # Allow mouse events even when not focused
        self.setMouseTracking(True)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent; border: none;")
        self.image_label.setScaledContents(False)
        layout.addWidget(self.image_label)

        self.setLayout(layout)

    def _load_pet_image(self) -> None:
        pet_name = self.config.settings.pet_name
        pixmap = self.resources.get_pet_image(pet_name)

        if pixmap is None or pixmap.isNull():
            # Fallback placeholder so the app still runs without assets
            pixmap = QPixmap(160, 160)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.magenta)
            painter.drawRect(2, 2, 155, 155)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No Image\n(add pet.png)")
            painter.end()
            logger.warning(
                "Pet image missing for '%s'. Place a transparent PNG at assets/pets/%s/pet.png",
                pet_name,
                pet_name,
            )

        self._original_pixmap = pixmap
        self._apply_scale()

    def _apply_scale(self) -> None:
        if self._original_pixmap.isNull():
            return

        target_size = self._original_pixmap.size() * self._scale
        scaled = self._original_pixmap.scaled(
            target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self.resize(scaled.size())
        self.setMinimumSize(scaled.size())
        self.setMaximumSize(scaled.size())  # keep exact size for clean transparency

    def _restore_geometry(self) -> None:
        s = self.config.settings
        self.move(int(s.pos_x), int(s.pos_y))

    # ------------------------------------------------------------------
    # Mouse interaction
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
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

        # Find current index and move to next/prev step
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
        logger.debug("Scale set to %.1f", self._scale)
        event.accept()
