"""Configuration manager. All settings go through ConfigManager."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.utils.paths import CONFIG_DIR, ensure_dirs
from src.utils.logger import get_logger

logger = get_logger("config")


@dataclass
class AppSettings:
    """Persistent application settings."""

    pos_x: int = 100
    pos_y: int = 100
    scale: float = 1.0
    pet_name: str = "Girl"
    volume: float = 0.8
    always_on_top: bool = True
    random_move: bool = False
    auto_start: bool = False


class ConfigManager:
    """Load, save and provide access to application configuration."""

    def __init__(self, config_path: Path | None = None) -> None:
        ensure_dirs()
        self._path = config_path or (CONFIG_DIR / "user_settings.json")
        self.settings = AppSettings()
        self.load()

    def load(self) -> None:
        """Load settings from JSON file."""
        if not self._path.exists():
            logger.info("No existing config, using defaults.")
            self.save()
            return
        try:
            data: dict[str, Any] = json.loads(self._path.read_text(encoding="utf-8"))
            for key, value in data.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            logger.info("Config loaded from %s", self._path)
        except Exception as exc:
            logger.exception("Failed to load config: %s", exc)

    def save(self) -> None:
        """Persist current settings to JSON."""
        try:
            self._path.write_text(
                json.dumps(asdict(self.settings), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            logger.debug("Config saved to %s", self._path)
        except Exception as exc:
            logger.exception("Failed to save config: %s", exc)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self.settings, key, default)

    def set(self, key: str, value: Any) -> None:
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save()
