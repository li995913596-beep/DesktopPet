"""System tray controller. Close window hides to tray; quit only from menu."""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QColor
from PySide6.QtWidgets import QSystemTrayIcon, QMenu

from src.core.config import ConfigManager
from src.utils.logger import get_logger

logger = get_logger("tray")


def _create_fallback_icon() -> QIcon:
    """Generate a simple coloured circle icon when no pet image is available."""
    pix = QPixmap(64, 64)
    pix.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QColor(255, 105, 180))
    painter.setPen(QColor(255, 255, 255))
    painter.drawEllipse(4, 4, 56, 56)
    painter.end()
    return QIcon(pix)


class TrayController(QObject):
    """Manage system tray icon and its context menu."""

    show_pet_requested = Signal()
    hide_pet_requested = Signal()
    quit_requested = Signal()

    def __init__(self, config: ConfigManager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.config = config

        self.tray = QSystemTrayIcon(parent)
        self.tray.setToolTip("DesktopPet")

        icon = self._load_pet_icon() or _create_fallback_icon()
        self.tray.setIcon(icon)

        self._build_menu()
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self._on_activated)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available on this platform.")
        else:
            self.tray.show()
            logger.info("System tray icon shown.")

    def _load_pet_icon(self) -> QIcon | None:
        from src.core.resource_manager import ResourceManager

        rm = ResourceManager()
        pix = rm.get_pet_image(self.config.settings.pet_name)
        if pix is None or pix.isNull():
            return None
        small = pix.scaled(
            64,
            64,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        return QIcon(small)

    def _build_menu(self) -> None:
        self.menu = QMenu()

        show_action = QAction("显示桌宠", self.menu)
        show_action.triggered.connect(self.show_pet_requested.emit)
        self.menu.addAction(show_action)

        hide_action = QAction("隐藏桌宠", self.menu)
        hide_action.triggered.connect(self.hide_pet_requested.emit)
        self.menu.addAction(hide_action)

        self.menu.addSeparator()

        settings_action = QAction("设置 (即将推出)", self.menu)
        settings_action.setEnabled(False)
        self.menu.addAction(settings_action)

        self.menu.addSeparator()

        quit_action = QAction("退出", self.menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        self.menu.addAction(quit_action)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_pet_requested.emit()

    def show_message(self, title: str, message: str, msecs: int = 3000) -> None:
        self.tray.showMessage(
            title, message, QSystemTrayIcon.MessageIcon.Information, msecs
        )
