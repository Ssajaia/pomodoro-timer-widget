from __future__ import annotations
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional


CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "PomodoroTimer")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
STATS_FILE = os.path.join(CONFIG_DIR, "stats.json")


@dataclass
class WindowConfig:
    x: Optional[int] = None
    y: Optional[int] = None
    width: int = 300
    height: int = 380
    compact: bool = False
    opacity: float = 1.0
    close_to_tray: bool = True


@dataclass
class TimerConfig:
    focus_minutes: int = 25
    short_break_minutes: int = 5
    long_break_minutes: int = 15
    sessions_before_long_break: int = 4
    auto_start_breaks: bool = True
    auto_start_focus: bool = False


@dataclass
class NotificationConfig:
    enabled: bool = True
    sound_enabled: bool = True
    custom_sound_path: Optional[str] = None


@dataclass
class AppConfig:
    window: WindowConfig = field(default_factory=WindowConfig)
    timer: TimerConfig = field(default_factory=TimerConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    theme: str = "dark"

    def save(self) -> None:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> "AppConfig":
        if not os.path.exists(CONFIG_FILE):
            return cls()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = cls()
            w = data.get("window", {})
            cfg.window = WindowConfig(**{k: v for k, v in w.items() if k in WindowConfig.__dataclass_fields__})
            t = data.get("timer", {})
            cfg.timer = TimerConfig(**{k: v for k, v in t.items() if k in TimerConfig.__dataclass_fields__})
            n = data.get("notifications", {})
            cfg.notifications = NotificationConfig(**{k: v for k, v in n.items() if k in NotificationConfig.__dataclass_fields__})
            cfg.theme = data.get("theme", "dark")
            return cfg
        except Exception:
            return cls()


@dataclass
class Stats:
    total_pomodoros: int = 0
    total_focus_minutes: int = 0
    daily: dict = field(default_factory=dict)

    def increment(self, focus_minutes: int) -> None:
        import datetime
        today = datetime.date.today().isoformat()
        self.total_pomodoros += 1
        self.total_focus_minutes += focus_minutes
        self.daily[today] = self.daily.get(today, 0) + 1

    def today_count(self) -> int:
        import datetime
        today = datetime.date.today().isoformat()
        return self.daily.get(today, 0)

    def save(self) -> None:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> "Stats":
        if not os.path.exists(STATS_FILE):
            return cls()
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(
                total_pomodoros=data.get("total_pomodoros", 0),
                total_focus_minutes=data.get("total_focus_minutes", 0),
                daily=data.get("daily", {}),
            )
        except Exception:
            return cls()
