"""Application entry point for DesktopPet."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from src.utils.logger import setup_logger
from src.utils.paths import PROJECT_ROOT
from src.core.config import ConfigManager
from src.ui.pet_window import PetWindow


def main() -> int:
    """Start the DesktopPet application.

    Returns:
        Exit code.
    """
    setup_logger()
    logger = setup_logger().__class__  # placeholder, use get_logger later

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = ConfigManager()
    window = PetWindow(config)
    window.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
