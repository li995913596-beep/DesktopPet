"""Transparent, frameless, always-on-top pet window with perfect alpha support."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QSize, Signal
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

# Target default display height in pixels
DEFAULT_TARGET_HEIGHT: int = 220


class PetWindow(QWidget):
    """Main desktop pet window.

    Design goals:
    - True per-pixel transparency (no white/black/gray rectangle)
    - Always on top, never steals focus
    - Left-drag move, wheel scale (persisted)
    - Close event hides to tray (does not quit)
    """

    # Emitted when user requests quit from tray or elsewhere
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

    # ------------------------------------------------------------------
    # Window flags & attributes (critical for transparency + focus)
    # ------------------------------------------------------------------

    def _setup_window_flags(self) -> None:
        """Frameless + translucent + always-on-top + no focus steal."""
        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool          # no taskbar button, less focus stealing
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setWindowFlags(flags)

        # Core transparency attributes
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        # Prevent any automatic background fill
        self.setAutoFillBackground(False)
        self.setMouseTracking(True)

    # ------------------------------------------------------------------
    # Image loading & scaling
    # ------------------------------------------------------------------

    def _load_pet_image(self) -> None:
        pet_name = self.config.settings.pet_name
        pixmap = self.resources.get_pet_image(pet_name)

        if pixmap is None or pixmap.isNull():
            # Transparent placeholder so the window itself stays fully transparent
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

        # If scale is still the old default (1.0) and image is large,
        # auto-fit to DEFAULT_TARGET_HEIGHT for first run comfort.
        if abs(self._scale - 1.0) < 1e-6 and pixmap.height() > DEFAULT_TARGET_HEIGHT:
            auto_scale = DEFAULT_TARGET_HEIGHT / float(pixmap.height())
            # Snap to nearest allowed step
            self._scale = min(SCALE_STEPS, key=lambda s: abs(s - auto_scale))
            self.config.set("scale", self._scale)
            logger.info("Auto-scaled to %.1f (target height ~%dpx)", self._scale, DEFAULT_TARGET_HEIGHT)

        self._apply_scale()

    def _apply_scale(self) -> None:
        if self._original_pixmap.isNull():
            return

        target = self._original_pixmap.size() * self._scale
        # High-quality smooth scaling for anti-aliased edges
        self._scaled_pixmap = self._original_pixmap.scaled(
            target,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        size = self._scaled_pixmap.size()
        self.resize(size)
        self.setFixedSize(size)  # exact size, no extra margins
        self.update()  # trigger repaint

    def _restore_geometry(self) -> None:
        s = self.config.settings
        self.move(int(s.pos_x), int(s.pos_y))

    # ------------------------------------------------------------------
    # Painting – the only place we draw, guarantees true transparency
    # ------------------------------------------------------------------

    def paintEvent(self, event: QPaintEvent) -> None:
        """Draw only the pixmap; everything else stays fully transparent."""
        if self._scaled_pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        # Critical: do NOT fill any background
        painter.drawPixmap(0, 0, self._scaled_pixmap)

    # ------------------------------------------------------------------
    # Mouse interaction
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Close behaviour: hide to tray, never quit from window close
    # ------------------------------------------------------------------

    def closeEvent(self, event: QCloseEvent) -> None:
        """Intercept close → hide instead of destroy."""
        event.ignore()
        self.hide()
        logger.info("Pet window hidden to tray.")

    def show_pet(self) -> None:
        """Show and raise the pet (called from tray)."""
        self.show()
        self.raise_()

    def set_always_on_top(self, enabled: bool) -> None:
        """Toggle always-on-top flag at runtime."""
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowType.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.show()  # required after flag change
        self.config.set("always_on_top", enabled)
