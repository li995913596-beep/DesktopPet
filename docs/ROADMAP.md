# Development Roadmap

| Version | Feature                          | Status      |
|---------|----------------------------------|-------------|
| V0.1    | Basic framework                  | Done        |
| V0.2    | Transparent window               | Done        |
| V0.3    | Pet display                      | Done        |
| V0.4    | Drag                             | Done        |
| V0.5    | Wheel scale                      | Done        |
| V0.6    | True transparency + Tray + size  | **Done**    |
| V0.7    | AnimationManager (frame folders) | Next        |
| V0.8    | State machine + Idle / Click     | Planned     |
| V0.9    | Context menu                     | Planned     |
| V1.0    | Multi-character + settings UI    | Planned     |
| V1.1    | Bubble system                    | Planned     |
| V1.2    | SoundManager                     | Planned     |
| V1.3    | Random behaviours / walk         | Planned     |
| V1.4    | PluginManager                    | Planned     |
| V1.5    | AI provider interface            | Planned     |
| V2.0    | Official release                 | Planned     |

## Immediate next work

1. AnimationManager that loads `assets/pets/<name>/animations/<state>/*.png`
2. Simple state machine (Idle ↔ Click ↔ Sleep …)
3. Right-click context menu on the pet
4. Full tray menu (switch character, always-on-top toggle, etc.)
