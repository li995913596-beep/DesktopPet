"""Application entry point for DesktopPet."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.utils.logger import setup_logger, get_logger
from src.utils.paths import ensure_dirs
from src.core.config import ConfigManager
from src.ui.pet_window import PetWindow
from src.ui.tray import TrayController


def main() -> int:
    """Start the DesktopPet application.

    Returns:
        Exit code.
    """
    ensure_dirs()
    setup_logger()
    logger = get_logger("app")
    logger.info("DesktopPet starting...")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # critical: tray keeps process alive
    app.setApplicationName("DesktopPet")
    app.setApplicationVersion("0.6.0")

    config = ConfigManager()

    # Main pet window
    window = PetWindow(config)

    # System tray
    tray = TrayController(config)
    tray.show_pet_requested.connect(window.show_pet)
    tray.quit_requested.connect(app.quit)

    # Also allow window to request quit (future menus)
    window.quit_requested.connect(app.quit)

    window.show()
    logger.info(
        "Pet window shown. "
        "Left-drag to move, wheel to scale, close → tray, tray menu → exit."
    )

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
