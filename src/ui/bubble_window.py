"""Independent floating bubble window (not clipped by pet window)."""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class BubbleWindow(QWidget):
    """Small always-on-top transparent window for speech bubbles."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setAutoFillBackground(False)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel()
        self.label.setStyleSheet(
            """
            QLabel {
                background: rgba(255, 255, 255, 235);
                color: #222;
                border: 1px solid rgba(0,0,0,40);
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 13px;
                font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            }
            """
        )
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self.hide()
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_text(self, text: str, duration_ms: int, anchor_global: QPoint) -> None:
        """Show bubble centered above the given global point (usually pet top-center)."""
        self.label.setText(text)
        self.label.adjustSize()
        self.adjustSize()

        x = anchor_global.x() - self.width() // 2
        y = anchor_global.y() - self.height() - 8
        self.move(x, y)
        self.show()
        self.raise_()

        self._hide_timer.stop()
        self._hide_timer.start(duration_ms)

    def clear(self) -> None:
        self._hide_timer.stop()
        self.hide()
