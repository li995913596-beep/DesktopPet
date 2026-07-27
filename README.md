# DesktopPet

A modern, modular, open-source desktop pet (桌宠) for Windows, built with Python 3.12+ and PySide6.

## Features (Roadmap)

- Transparent, frameless, always-on-top pet window
- Drag, scale, click animations, idle animations
- System tray, context menus, settings persistence
- Multi-character support
- Bubble system, sound, weather, reminders
- Plugin system, AI chat interfaces
- Auto-update via GitHub Releases

## Requirements

- Python 3.12+
- PySide6

## Installation

```bash
pip install -r requirements.txt
python -m src.app
```

## Project Structure

```
DesktopPet/
├── assets/
│   └── pets/
│       └── Girl/
├── config/
├── docs/
├── plugins/
├── sounds/
├── src/
│   ├── app.py
│   ├── core/
│   ├── ui/
│   └── utils/
└── ...
```

## Development

Follow Git Flow. Keep the project always runnable. See `docs/` for details.

## License

MIT (planned)
