from __future__ import annotations
import os
import sys
import threading
from typing import Optional

from core.config import NotificationConfig
from core.timer import Phase


def _play_beep(frequency: int = 880, duration_ms: int = 200) -> None:
    if sys.platform != "win32":
        return
    try:
        import winsound
        winsound.Beep(frequency, duration_ms)
    except Exception:
        pass


def _play_sound_file(path: str) -> None:
    if sys.platform != "win32":
        return
    try:
        import winsound
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass


def _win_notify(title: str, message: str, icon_path: Optional[str] = None) -> None:
    if sys.platform != "win32":
        return
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(title, message, icon_path=icon_path, duration=5, threaded=True)
    except ImportError:
        _fallback_notify(title, message)
    except Exception:
        pass


def _fallback_notify(title: str, message: str) -> None:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40 | 0x1000)
    except Exception:
        pass


class NotificationManager:
    def __init__(self, config: NotificationConfig, icon_path: Optional[str] = None) -> None:
        self.config = config
        self.icon_path = icon_path
        self._lock = threading.Lock()

    def update_config(self, config: NotificationConfig) -> None:
        self.config = config

    def notify_phase(self, phase: Phase) -> None:
        if not self.config.enabled:
            return
        titles = {
            Phase.FOCUS: ("Focus Time", "Time to focus for 25 minutes."),
            Phase.SHORT_BREAK: ("Short Break", "Take a 5 minute break."),
            Phase.LONG_BREAK: ("Long Break", "Great work! Take a 15 minute break."),
        }
        title, message = titles[phase]
        threading.Thread(
            target=self._send,
            args=(title, message),
            daemon=True,
        ).start()

    def notify_session_end(self, phase: Phase) -> None:
        if not self.config.enabled:
            return
        msgs = {
            Phase.FOCUS: ("Focus Complete!", "Session done. Take a break."),
            Phase.SHORT_BREAK: ("Break Over", "Ready to focus again?"),
            Phase.LONG_BREAK: ("Long Break Over", "Ready for another round?"),
        }
        title, message = msgs[phase]
        threading.Thread(
            target=self._send,
            args=(title, message),
            daemon=True,
        ).start()

    def _send(self, title: str, message: str) -> None:
        with self._lock:
            if self.config.sound_enabled:
                self._play_notification_sound()
            _win_notify(title, message, self.icon_path)

    def _play_notification_sound(self) -> None:
        if self.config.custom_sound_path and os.path.exists(self.config.custom_sound_path):
            _play_sound_file(self.config.custom_sound_path)
        else:
            _play_beep(880, 150)
            import time
            time.sleep(0.2)
            _play_beep(1100, 150)
