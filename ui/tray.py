from __future__ import annotations
import sys
import threading
from typing import Callable, Optional


class TrayIcon:
    def __init__(
        self,
        icon_path: str,
        tooltip: str,
        on_restore: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self._icon_path = icon_path
        self._tooltip = tooltip
        self._on_restore = on_restore
        self._on_quit = on_quit
        self._icon = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        if sys.platform != "win32":
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def update_tooltip(self, tooltip: str) -> None:
        self._tooltip = tooltip
        if self._icon:
            try:
                self._icon.title = tooltip
            except Exception:
                pass

    def _run(self) -> None:
        try:
            import pystray
            from PIL import Image as PILImage
            img = PILImage.open(self._icon_path)
            menu = pystray.Menu(
                pystray.MenuItem("Show", self._restore, default=True),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", self._quit),
            )
            self._icon = pystray.Icon(
                "pomodoro",
                img,
                self._tooltip,
                menu=menu,
            )
            self._icon.run()
        except Exception:
            pass

    def _restore(self, icon=None, item=None) -> None:
        if self._icon:
            self._icon.stop()
            self._icon = None
        self._on_restore()

    def _quit(self, icon=None, item=None) -> None:
        if self._icon:
            self._icon.stop()
            self._icon = None
        self._on_quit()
