"""Application entry point – wires the living Pet to a thin Renderer."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from src.utils.logger import setup_logger, get_logger
from src.utils.paths import ensure_dirs
from src.core.config import ConfigManager
from src.core.pet import Pet
from src.ui.pet_window import PetWindow
from src.ui.tray import TrayController


def main() -> int:
    ensure_dirs()
    setup_logger()
    logger = get_logger("app")
    logger.info("DesktopPet (QQ-Pet style) starting...")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("DesktopPet")
    app.setApplicationVersion("0.7.1")

    config = ConfigManager()

    # The living core
    pet = Pet(config)

    # Thin view
    window = PetWindow(config, pet)

    tray = TrayController(config)
    tray.show_pet_requested.connect(window.show_pet)
    tray.hide_pet_requested.connect(window.hide)
    tray.quit_requested.connect(lambda: (pet.shutdown(), app.quit()))
    window.quit_requested.connect(lambda: (pet.shutdown(), app.quit()))

    window.show()
    logger.info(
        "Pet is alive. "
        "It will idle / look / yawn / walk / talk on its own. "
        "Click = reaction + bubble. Close = tray."
    )

    code = app.exec()
    pet.shutdown()
    return code


if __name__ == "__main__":
    sys.exit(main())
