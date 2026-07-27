# DesktopPet

A modern, modular, open-source desktop pet (桌宠) for Windows, built with Python 3.12+ and PySide6.

## Current Status (V0.5)

- Transparent, frameless, always-on-top window
- Pet image display (place `pet.png` under `assets/pets/Girl/`)
- Left-mouse drag
- Mouse-wheel scale (0.5x ~ 2.0x, persisted)
- Settings persisted to JSON
- Modular architecture ready for animations, tray, plugins, AI

## Quick Start

1. Clone the repo
2. Create a virtual environment (recommended)
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. **Important**: Put a transparent PNG named `pet.png` into:

```
assets/pets/Girl/pet.png
```

(If missing, a simple placeholder will be shown.)

5. Run:

```bash
python -m src.app
```

## Features (Roadmap)

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Project Structure

```
DesktopPet/
├── assets/
│   └── pets/
│       └── Girl/
│           ├── pet.png          # <-- put your image here
│           ├── config.json
│           ├── animations/
│           └── sounds/
├── config/
├── docs/
├── plugins/
├── sounds/
├── src/
│   ├── app.py
│   ├── core/
│   │   ├── config.py
│   │   ├── animation.py
│   │   ├── pet_manager.py
│   │   └── resource_manager.py
│   ├── ui/
│   │   ├── pet_window.py
│   │   ├── tray.py
│   │   └── bubble.py
│   └── utils/
│       ├── logger.py
│       └── paths.py
└── requirements.txt
```

## Development Principles

- Python 3.12+ with full type annotations
- Dataclasses + OOP
- No circular imports
- Single responsibility, high cohesion, low coupling
- All paths via `paths.py`, all config via `ConfigManager`, all resources via `ResourceManager`
- Keep every commit runnable

## License

MIT (planned)
