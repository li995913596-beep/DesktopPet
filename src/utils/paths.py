"""Centralized path management. Never hard-code resource paths elsewhere."""

from __future__ import annotations

from pathlib import Path

# Project root: DesktopPet/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

ASSETS_DIR = PROJECT_ROOT / "assets"
PETS_DIR = ASSETS_DIR / "pets"
CONFIG_DIR = PROJECT_ROOT / "config"
PLUGINS_DIR = PROJECT_ROOT / "plugins"
SOUNDS_DIR = PROJECT_ROOT / "sounds"
LOGS_DIR = PROJECT_ROOT / "logs"
DOCS_DIR = PROJECT_ROOT / "docs"


def get_pet_dir(pet_name: str) -> Path:
    """Return the directory for a given pet character."""
    return PETS_DIR / pet_name


def ensure_dirs() -> None:
    """Create essential directories if they do not exist."""
    for d in (CONFIG_DIR, LOGS_DIR, PLUGINS_DIR, SOUNDS_DIR):
        d.mkdir(parents=True, exist_ok=True)
