# DesktopPet

A modern, modular, open-source desktop pet (桌宠) for Windows, built with **Python 3.12+** and **PySide6**.

## Current Status (V0.5.1)

- Transparent, frameless, always-on-top window (no focus steal)
- Pet image display from `assets/pets/<name>/pet.png`
- Left-mouse drag + position persistence
- Mouse-wheel scale (0.5× ~ 2.0× with nice steps) + scale persistence
- Settings saved to JSON via `ConfigManager`
- Clean modular architecture ready for animations / tray / plugins / AI

## Quick Start

```bash
git clone https://github.com/li995913596-beep/DesktopPet.git
cd DesktopPet
pip install -r requirements.txt
```

### Add the pet image (required for best experience)

Place a **transparent PNG** named `pet.png` here:

```
assets/pets/Girl/pet.png
```

The provided character is a cute long-haired chibi girl (grey crop top + blue jeans).  
You can upload it via GitHub web UI (drag & drop into the folder) or locally:

```bash
# after cloning
cp /path/to/your/pet.png assets/pets/Girl/pet.png
```

If the file is missing the app still runs and shows a simple placeholder.

Then run:

```bash
python -m src.app
```

**Controls**

| Action              | How                          |
|---------------------|------------------------------|
| Move the pet        | Left-click drag              |
| Scale               | Mouse wheel                  |
| Exit (for now)      | Close from task manager / Ctrl+C in terminal |

## Project Structure

```
DesktopPet/
├── assets/pets/Girl/     # one folder per character
│   ├── pet.png           # main image (transparent PNG)
│   └── config.json
├── config/               # user settings (auto-created)
├── docs/
├── plugins/              # future plugins
├── src/
│   ├── app.py            # entry point
│   ├── core/             # config / resources / animation / pet_manager
│   ├── ui/               # pet_window / tray / bubble
│   └── utils/            # logger / paths
└── requirements.txt
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

Next planned steps: Idle animation → Click animation → Context menu → System tray → Multi-character → ...

## Development Rules

- Python 3.12+, full type annotations, dataclasses
- No circular imports, no magic numbers, no hard-coded paths
- All paths via `utils/paths.py`, config via `ConfigManager`, resources via `ResourceManager`
- Keep every commit runnable
- Single responsibility, high cohesion, low coupling

## License

MIT (planned)
