"""High-level pet lifecycle and behavior coordinator."""

from __future__ import annotations

from src.core.config import ConfigManager
from src.core.resource_manager import ResourceManager
from src.core.animation import AnimationManager
from src.utils.logger import get_logger

logger = get_logger("pet_manager")


class PetManager:
    """Coordinate resources, animation and configuration for the active pet."""

    def __init__(self, config: ConfigManager) -> None:
        self.config = config
        self.resources = ResourceManager()
        self.animation = AnimationManager()
        self.pet_name = config.settings.pet_name

    def load_pet(self, name: str | None = None) -> None:
        """Switch or reload the current pet character."""
        if name:
            self.pet_name = name
            self.config.set("pet_name", name)
        logger.info("Active pet: %s", self.pet_name)
