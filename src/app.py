"""Application entry point for DesktopPet."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.utils.logger import setup_logger, get_logger
from src.utils.paths import ensure_dirs
from src.core.config import ConfigManager
from src.ui.pet_window import PetWindow


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
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("DesktopPet")
    app.setApplicationVersion("0.5.0")

    config = ConfigManager()
    window = PetWindow(config)
    window.show()

    logger.info("Pet window shown. Drag with left mouse, scroll to scale.")
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
