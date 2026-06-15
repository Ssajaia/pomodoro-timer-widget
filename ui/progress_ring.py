from __future__ import annotations
import math
import tkinter as tk
from typing import Optional

from ui.themes import Theme


class ProgressRing(tk.Canvas):
    def __init__(
        self,
        parent: tk.Widget,
        size: int,
        theme: Theme,
        **kwargs,
    ) -> None:
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=theme.bg,
            highlightthickness=0,
            **kwargs,
        )
        self._size = size
        self._theme = theme
        self._progress: float = 1.0
        self._phase_color: str = theme.progress_fill
        self._draw()

    def set_theme(self, theme: Theme) -> None:
        self._theme = theme
        self.configure(bg=theme.bg)
        self._draw()

    def set_progress(self, progress: float, color: Optional[str] = None) -> None:
        self._progress = max(0.0, min(1.0, progress))
        if color:
            self._phase_color = color
        self._draw()

    def _draw(self) -> None:
        self.delete("all")
        t = self._theme
        s = self._size
        cx, cy = s / 2, s / 2
        stroke = max(8, int(s * 0.06))
        r = (s - stroke * 2) / 2

        self.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=0, extent=359.9999,
            style="arc", outline=t.progress_track,
            width=stroke,
        )

        if self._progress > 0.002:
            extent = self._progress * 360.0
            self.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=90, extent=-extent,
                style="arc", outline=self._phase_color,
                width=stroke,
            )

        dot_angle = math.radians(90 - self._progress * 360)
        dot_x = cx + r * math.cos(dot_angle)
        dot_y = cy - r * math.sin(dot_angle)
        dot_r = stroke / 2 + 1
        self.create_oval(
            dot_x - dot_r, dot_y - dot_r,
            dot_x + dot_r, dot_y + dot_r,
            fill=self._phase_color, outline="",
        )
