"""Transparent, frameless, always-on-top pet window."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QSize
from PySide6.QtGui import QPixmap, QMouseEvent, QWheelEvent, QPainter
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout

from src.core.config import ConfigManager
from src.core.resource_manager import ResourceManager
from src.utils.logger import get_logger

logger = get_logger("pet_window")


class PetWindow(QWidget):
    """Main desktop pet window.

    Features (V0.x):
    - Frameless, transparent background
    - Always on top
    - Does not steal focus
    - Draggable by left mouse button
    - Scale via mouse wheel (persisted)
    """

    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self.config = config
        self.resources = ResourceManager()
        self._drag_pos: QPoint | None = None
        self._scale = config.settings.scale

        self._setup_window_flags()
        self._setup_ui()
        self._load_pet_image()
        self._restore_geometry()

    def _setup_window_flags(self) -> None:
        """Configure frameless, transparent, always-on-top, no-focus window."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # avoid taskbar / focus stealing on Windows
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        layout.addWidget(self.image_label)

        self.setLayout(layout)

    def _load_pet_image(self) -> None:
        pet_name = self.config.settings.pet_name
        pixmap = self.resources.get_pet_image(pet_name)
        if pixmap is None:
            # Fallback placeholder so the app still runs
            pixmap = QPixmap(128, 128)
            pixmap.fill(Qt.GlobalColor.transparent)
            painter = QPainter(pixmap)
            painter.setPen(Qt.GlobalColor.magenta)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "No Image")
            painter.end()
            logger.warning("Using placeholder image for pet '%s'", pet_name)

        self._original_pixmap = pixmap
        self._apply_scale()

    def _apply_scale(self) -> None:
        if self._original_pixmap.isNull():
            return
        scaled = self._original_pixmap.scaled(
            self._original_pixmap.size() * self._scale,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)
        self.resize(scaled.size())

    def _restore_geometry(self) -> None:
        s = self.config.settings
        self.move(s.pos_x, s.pos_y)

    # --- Mouse interaction ---

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self._drag_pos = None
            # Persist position
            pos = self.pos()
            self.config.set("pos_x", pos.x())
            self.config.set("pos_y", pos.y())
            event.accept()

    def wheelEvent(self, event: QWheelEvent) -> None:
        delta = event.angleDelta().y()
        step = 0.1
        if delta > 0:
            self._scale = min(2.0, self._scale + step)
        else:
            self._scale = max(0.5, self._scale - step)

        # Snap to nice values
        nice = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5, 1.8, 2.0]
        self._scale = min(nice, key=lambda x: abs(x - self._scale))

        self._apply_scale()
        self.config.set("scale", self._scale)
        logger.debug("Scale set to %.1f", self._scale)
        event.accept()
