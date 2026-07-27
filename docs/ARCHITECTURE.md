# Architecture (V0.7+)

## Goal

A living QQ-Pet style companion, **not** a floating PNG.

## Core principle

```
Pet (aggregate root)
  ├── PetBrain          # decides what to do
  ├── EmotionManager    # mood affects probabilities
  ├── BehaviorManager   # weighted random behaviors
  ├── StateMachine      # current activity
  ├── AnimationManager  # visual output (procedural → frames → Live2D)
  ├── BubbleManager     # speech
  └── Scheduler         # time-driven ticks
```

`PetWindow` is only a **Renderer + input forwarder**.  
It must never contain decision logic, emotion, or behavior selection.

## Why this shape (not pure Behavior Tree yet)

- Clear ownership and easy debugging for an open-source project
- Emotion → weight multipliers is enough to make mood feel real
- Scheduler keeps all timers in one place
- Can evolve any Behavior into a Behavior-Tree node later without rewriting the rest

## Data flow

1. `Scheduler` ticks → `PetBrain._think`
2. Brain asks `BehaviorManager.select_and_start()`
3. Behavior sets `StateMachine` + tells `AnimationManager.play`
4. AnimationManager emits `frame_changed` → PetWindow paints
5. User click → `Pet.handle_click` → Brain forces reaction + bubble

## Extension points

| Future feature | Where it plugs in                          |
|----------------|--------------------------------------------|
| Weather        | EmotionManager + Behavior weights          |
| AI chat        | BubbleManager + new Behavior               |
| Needs (hunger) | EmotionManager + Scheduler                 |
| Frame anims    | AnimationManager loads folder sequences    |
| Live2D         | AnimationManager backend swap              |
| Plugins        | new Behaviors registered into BehaviorManager |

## Rules

- No circular imports
- No business logic in `ui/`
- All paths via `utils/paths.py`
- All settings via `ConfigManager`
- Keep every commit runnable
