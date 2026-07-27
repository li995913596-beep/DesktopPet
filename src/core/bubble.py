"""BubbleManager – owns what the pet says and when."""

from __future__ import annotations

import random
from typing import List, Optional

from PySide6.QtCore import QObject, Signal

from src.core.emotion import Emotion, EmotionManager
from src.utils.logger import get_logger

logger = get_logger("bubble")

# Simple phrase pools – later loaded from config / character files
PHRASES: dict[str, List[str]] = {
    "neutral": ["你好~", "今天也要加油哦", "摸摸头~", "在吗？", "嘿嘿"],
    "happy": ["好开心！", "耶~", "一起玩吧！", "最喜欢你了"],
    "sleepy": ["好困啊...", "Zzz", "再睡五分钟...", "打哈欠~"],
    "bored": ["好无聊...", "陪我玩嘛", "有什么好玩的吗"],
    "excited": ["哇！", "太棒了！", "冲冲冲！"],
}


class BubbleManager(QObject):
    """Decides text and emits show/hide requests. UI layer only displays."""

    show_text = Signal(str, int)  # text, duration_ms
    hide = Signal()

    def __init__(self, emotion: EmotionManager, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._emotion = emotion

    def say_random(self) -> None:
        e = self._emotion.current
        key = e.name.lower() if e.name.lower() in PHRASES else "neutral"
        pool = PHRASES.get(key, PHRASES["neutral"])
        text = random.choice(pool)
        duration = 2500 + random.randint(0, 1500)
        logger.debug("Bubble: %s", text)
        self.show_text.emit(text, duration)

    def say(self, text: str, duration_ms: int = 3000) -> None:
        self.show_text.emit(text, duration_ms)

    def clear(self) -> None:
        self.hide.emit()
