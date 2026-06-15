from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

from core.config import AppConfig
from ui.themes import Theme


class SettingsDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        config: AppConfig,
        theme: Theme,
        on_save: Callable[[AppConfig], None],
    ) -> None:
        super().__init__(parent)
        self._config = config
        self._theme = theme
        self._on_save = on_save

        self.title("Settings")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self.configure(bg=theme.bg)

        self._build_ui()
        self._center(parent)

    def _center(self, parent: tk.Tk) -> None:
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        w, h = self.winfo_width(), self.winfo_height()
        self.geometry(f"+{px - w // 2}+{py - h // 2}")

    def _build_ui(self) -> None:
        t = self._theme
        c = self._config

        pad = dict(padx=16, pady=6)
        label_opts = dict(bg=t.bg, fg=t.fg, font=("Segoe UI", 10))
        entry_opts = dict(
            bg=t.input_bg,
            fg=t.input_fg,
            insertbackground=t.fg,
            relief="flat",
            highlightthickness=1,
            highlightcolor=t.accent,
            highlightbackground=t.border,
            font=("Segoe UI", 10),
            width=8,
        )
        header_font = ("Segoe UI", 11, "bold")

        def section(text: str) -> None:
            tk.Label(self, text=text, bg=t.bg, fg=t.accent, font=header_font).pack(
                anchor="w", padx=16, pady=(12, 2)
            )
            tk.Frame(self, bg=t.border, height=1).pack(fill="x", padx=16)

        section("Timer Durations")

        row = tk.Frame(self, bg=t.bg)
        row.pack(fill="x", **pad)
        tk.Label(row, text="Focus (min)", **label_opts).pack(side="left")
        self._focus_var = tk.StringVar(value=str(c.timer.focus_minutes))
        tk.Entry(row, textvariable=self._focus_var, **entry_opts).pack(side="right")

        row = tk.Frame(self, bg=t.bg)
        row.pack(fill="x", **pad)
        tk.Label(row, text="Short Break (min)", **label_opts).pack(side="left")
        self._short_var = tk.StringVar(value=str(c.timer.short_break_minutes))
        tk.Entry(row, textvariable=self._short_var, **entry_opts).pack(side="right")

        row = tk.Frame(self, bg=t.bg)
        row.pack(fill="x", **pad)
        tk.Label(row, text="Long Break (min)", **label_opts).pack(side="left")
        self._long_var = tk.StringVar(value=str(c.timer.long_break_minutes))
        tk.Entry(row, textvariable=self._long_var, **entry_opts).pack(side="right")

        row = tk.Frame(self, bg=t.bg)
        row.pack(fill="x", **pad)
        tk.Label(row, text="Sessions before Long Break", **label_opts).pack(side="left")
        self._sessions_var = tk.StringVar(value=str(c.timer.sessions_before_long_break))
        tk.Entry(row, textvariable=self._sessions_var, **entry_opts).pack(side="right")

        section("Auto-start")

        self._auto_break_var = tk.BooleanVar(value=c.timer.auto_start_breaks)
        self._check(self, "Auto-start breaks", self._auto_break_var)

        self._auto_focus_var = tk.BooleanVar(value=c.timer.auto_start_focus)
        self._check(self, "Auto-start focus sessions", self._auto_focus_var)

        section("Appearance")

        row = tk.Frame(self, bg=t.bg)
        row.pack(fill="x", **pad)
        tk.Label(row, text="Theme", **label_opts).pack(side="left")
        self._theme_var = tk.StringVar(value=c.theme)
        cb = tk.OptionMenu(row, self._theme_var, "dark", "light")
        cb.configure(
            bg=t.input_bg, fg=t.input_fg,
            activebackground=t.bg_secondary, activeforeground=t.fg,
            relief="flat", bd=0, highlightthickness=0,
            font=("Segoe UI", 10),
        )
        cb["menu"].configure(bg=t.input_bg, fg=t.input_fg, font=("Segoe UI", 10))
        cb.pack(side="right")

        row = tk.Frame(self, bg=t.bg)
        row.pack(fill="x", **pad)
        tk.Label(row, text="Opacity", **label_opts).pack(side="left")
        self._opacity_var = tk.DoubleVar(value=c.window.opacity)
        tk.Scale(
            row, from_=0.3, to=1.0, resolution=0.05,
            variable=self._opacity_var, orient="horizontal",
            bg=t.bg, fg=t.fg, troughcolor=t.bg_secondary,
            highlightthickness=0, bd=0, length=120,
        ).pack(side="right")

        self._close_tray_var = tk.BooleanVar(value=c.window.close_to_tray)
        self._check(self, "Close button minimizes to tray", self._close_tray_var)

        tk.Frame(self, bg=t.border, height=1).pack(fill="x", padx=16, pady=(12, 0))

        btn_row = tk.Frame(self, bg=t.bg)
        btn_row.pack(fill="x", padx=16, pady=12)

        tk.Button(
            btn_row, text="Cancel", command=self.destroy,
            bg=t.bg_secondary, fg=t.fg_secondary, relief="flat",
            font=("Segoe UI", 10), padx=16, pady=6,
            activebackground=t.border, activeforeground=t.fg, cursor="hand2",
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btn_row, text="Save", command=self._save,
            bg=t.accent, fg=t.button_fg, relief="flat",
            font=("Segoe UI", 10, "bold"), padx=16, pady=6,
            activebackground=t.accent_hover, activeforeground=t.button_fg, cursor="hand2",
        ).pack(side="right")

    def _check(self, parent: tk.Widget, text: str, var: tk.BooleanVar) -> None:
        t = self._theme
        row = tk.Frame(parent, bg=t.bg)
        row.pack(fill="x", padx=16, pady=4)
        tk.Checkbutton(
            row, text=text, variable=var,
            bg=t.bg, fg=t.fg, selectcolor=t.bg_secondary,
            activebackground=t.bg, activeforeground=t.fg,
            relief="flat", bd=0, highlightthickness=0,
            font=("Segoe UI", 10),
        ).pack(side="left")

    def _save(self) -> None:
        try:
            focus = int(self._focus_var.get())
            short = int(self._short_var.get())
            long_ = int(self._long_var.get())
            sessions = int(self._sessions_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Timer durations must be whole numbers.", parent=self)
            return

        if not (1 <= focus <= 120 and 1 <= short <= 60 and 1 <= long_ <= 120 and 1 <= sessions <= 20):
            messagebox.showerror("Invalid Input", "Values out of allowed range.", parent=self)
            return

        self._config.timer.focus_minutes = focus
        self._config.timer.short_break_minutes = short
        self._config.timer.long_break_minutes = long_
        self._config.timer.sessions_before_long_break = sessions
        self._config.timer.auto_start_breaks = self._auto_break_var.get()
        self._config.timer.auto_start_focus = self._auto_focus_var.get()
        self._config.theme = self._theme_var.get()
        self._config.window.opacity = round(self._opacity_var.get(), 2)
        self._config.window.close_to_tray = self._close_tray_var.get()

        self._on_save(self._config)
        self.destroy()