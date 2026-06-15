from __future__ import annotations
from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    name: str
    bg: str
    bg_secondary: str
    bg_tertiary: str
    fg: str
    fg_secondary: str
    accent: str
    accent_hover: str
    accent_break: str
    accent_long: str
    button_bg: str
    button_fg: str
    button_hover: str
    border: str
    progress_track: str
    progress_fill: str
    title_bar_bg: str
    title_bar_fg: str
    input_bg: str
    input_fg: str
    danger: str


THEMES: Dict[str, Theme] = {
    "dark": Theme(
        name="dark",
        bg="#1a1a2e",
        bg_secondary="#16213e",
        bg_tertiary="#0f3460",
        fg="#e2e8f0",
        fg_secondary="#94a3b8",
        accent="#e85d5d",
        accent_hover="#f07070",
        accent_break="#4ade80",
        accent_long="#60a5fa",
        button_bg="#e85d5d",
        button_fg="#ffffff",
        button_hover="#f07070",
        border="#334155",
        progress_track="#1e293b",
        progress_fill="#e85d5d",
        title_bar_bg="#0f172a",
        title_bar_fg="#e2e8f0",
        input_bg="#1e293b",
        input_fg="#e2e8f0",
        danger="#ef4444",
    ),
    "light": Theme(
        name="light",
        bg="#f8fafc",
        bg_secondary="#f1f5f9",
        bg_tertiary="#e2e8f0",
        fg="#0f172a",
        fg_secondary="#475569",
        accent="#dc2626",
        accent_hover="#ef4444",
        accent_break="#16a34a",
        accent_long="#2563eb",
        button_bg="#dc2626",
        button_fg="#ffffff",
        button_hover="#ef4444",
        border="#cbd5e1",
        progress_track="#e2e8f0",
        progress_fill="#dc2626",
        title_bar_bg="#1e293b",
        title_bar_fg="#f8fafc",
        input_bg="#ffffff",
        input_fg="#0f172a",
        danger="#dc2626",
    ),
}


def get_theme(name: str) -> Theme:
    return THEMES.get(name, THEMES["dark"])
