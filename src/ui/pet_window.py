"""Thin Renderer + input forwarder + soft shadow for depth."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, Signal, QTimer
from PySide6.QtGui import (
    QPixmap,
    QMouseEvent,
    QWheelEvent,
    QPainter,
    QPaintEvent,
    QCloseEvent,
    QColor,
)
from PySide6.QtWidgets import QWidget

from src.core.config import ConfigManager
from src.core.pet import Pet
from src.ui.bubble_window import BubbleWindow
from src.utils.logger import get_logger

logger = get_logger("pet_window")

SCALE_STEPS: list[float] = [0.8, 0.9, 1.0, 1.2, 1.5, 2.0]
DEFAULT_TARGET_HEIGHT: int = 150


class PetWindow(QWidget):
    quit_requested = Signal()

    def __init__(self, config: ConfigManager, pet: Pet) -> None:
        super().__init__()
        self.config = config
        self.pet = pet
        self._drag_pos: QPoint | None = None
        self._scale: float = float(config.settings.scale)
        self._pixmap = QPixmap()
        self._offset = QPoint(0, 0)
        self._base_size = None  # type: ignore

        self.bubble_win = BubbleWindow()

        self._setup_window_flags()
        self._connect_pet()
        self._restore_geometry()

    def _setup_window_flags(self) -> None:
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

    def _connect_pet(self) -> None:
        self.pet.frame_changed.connect(self._on_frame)
        self.pet.bubble_show.connect(self._on_bubble_show)
        self.pet.bubble_hide.connect(self._on_bubble_hide)
        self.pet.request_move.connect(self._on_request_move)

    def _on_frame(self, pixmap: QPixmap, offset: QPoint) -> None:
        if pixmap.isNull():
            return

        if self._base_size is None or abs(self._base_size.height() - pixmap.height()) > 2:
            self._base_size = pixmap.size()
            current_h = pixmap.height() * self._scale
            if current_h > DEFAULT_TARGET_HEIGHT * 1.1 or abs(self._scale - 1.0) < 1e-6:
                auto = DEFAULT_TARGET_HEIGHT / float(max(pixmap.height(), 1))
                self._scale = min(SCALE_STEPS, key=lambda s: abs(s - auto))
                self.config.set("scale", self._scale)

        scaled = pixmap.scaled(
            pixmap.size() * self._scale,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._pixmap = scaled
        self._offset = QPoint(int(offset.x() * self._scale), int(offset.y() * self._scale))

        # Extra room at bottom for soft shadow
        shadow_pad = 10
        self.resize(scaled.width(), scaled.height() + shadow_pad)
        self.setFixedSize(scaled.width(), scaled.height() + shadow_pad)
        self.update()

    def _on_bubble_show(self, text: str, duration_ms: int) -> None:
        # Anchor: top-center of pet in global coordinates
        top_center = self.mapToGlobal(QPoint(self.width() // 2, 0))
        self.bubble_win.show_text(text, duration_ms, top_center)

    def _on_bubble_hide(self) -> None:
        self.bubble_win.clear()

    def _on_request_move(self, dx: int, dy: int) -> None:
        pos = self.pos()
        self.move(pos.x() + dx, pos.y() + dy)
        self.config.set("pos_x", self.pos().x())
        self.config.set("pos_y", self.pos().y())

    def paintEvent(self, event: QPaintEvent) -> None:
        if self._pixmap.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        # Soft drop shadow for slight 3D depth
        shadow = QPixmap(self._pixmap.size())
        shadow.fill(Qt.GlobalColor.transparent)
        sp = QPainter(shadow)
        sp.setOpacity(0.25)
        sp.drawPixmap(0, 0, self._pixmap)
        sp.end()
        # Blur-ish by drawing offset multiple times
        for dx, dy in ((2, 3), (3, 5), (1, 4)):
            painter.setOpacity(0.12)
            painter.drawPixmap(self._offset.x() + dx, self._offset.y() + dy, shadow)
        painter.setOpacity(1.0)

        painter.drawPixmap(self._offset, self._pixmap)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self.pet.handle_click()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            self.pet.handle_drag()
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
            idx = min(range(len(SCALE_STEPS)), key=lambda i: abs(SCALE_STEPS[i] - self._scale))
        if delta > 0:
            idx = min(idx + 1, len(SCALE_STEPS) - 1)
        else:
            idx = max(idx - 1, 0)
        self._scale = SCALE_STEPS[idx]
        self.config.set("scale", self._scale)
        self._base_size = None
        event.accept()

    def closeEvent(self, event: QCloseEvent) -> None:
        event.ignore()
        self.hide()
        self.bubble_win.hide()

    def show_pet(self) -> None:
        self.show()
        self.raise_()

    def _restore_geometry(self) -> None:
        s = self.config.settings
        self.move(int(s.pos_x), int(s.pos_y))
