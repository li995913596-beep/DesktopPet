"""Lightweight task scheduler driven by QTimer."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from PySide6.QtCore import QObject, QTimer

from src.utils.logger import get_logger

logger = get_logger("scheduler")


class Scheduler(QObject):
    """Register named periodic or one-shot callbacks.

    All long-running autonomy is driven from here so PetBrain
    does not need to manage timers itself.
    """

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._timers: Dict[str, QTimer] = {}

    def every(self, name: str, interval_ms: int, callback: Callable[[], None]) -> None:
        """Call *callback* every *interval_ms* milliseconds."""
        self.cancel(name)
        timer = QTimer(self)
        timer.setInterval(interval_ms)
        timer.timeout.connect(callback)
        timer.start()
        self._timers[name] = timer
        logger.debug("Scheduler.every %s = %dms", name, interval_ms)

    def once(self, name: str, delay_ms: int, callback: Callable[[], None]) -> None:
        """Call *callback* once after *delay_ms*."""
        self.cancel(name)
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(delay_ms)
        timer.timeout.connect(callback)
        timer.start()
        self._timers[name] = timer

    def cancel(self, name: str) -> None:
        timer = self._timers.pop(name, None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()

    def cancel_all(self) -> None:
        for name in list(self._timers):
            self.cancel(name)
