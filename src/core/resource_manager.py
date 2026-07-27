"""Centralized resource loading (images, sounds, configs)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtGui import QPixmap

from src.utils.paths import get_pet_dir
from src.utils.logger import get_logger

logger = get_logger("resource")


class ResourceManager:
    """Load and cache pet resources."""

    def __init__(self) -> None:
        self._pixmap_cache: dict[str, QPixmap] = {}

    def get_pet_image(self, pet_name: str, filename: str = "pet.png") -> Optional[QPixmap]:
        """Load the main pet image.

        Args:
            pet_name: Character folder name.
            filename: Image file name.

        Returns:
            QPixmap or None if missing.
        """
        key = f"{pet_name}/{filename}"
        if key in self._pixmap_cache:
            return self._pixmap_cache[key]

        path = get_pet_dir(pet_name) / filename
        if not path.exists():
            logger.warning("Pet image not found: %s", path)
            return None

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            logger.error("Failed to load pixmap: %s", path)
            return None

        self._pixmap_cache[key] = pixmap
        logger.debug("Loaded pet image: %s", path)
        return pixmap

    def clear_cache(self) -> None:
        self._pixmap_cache.clear()
