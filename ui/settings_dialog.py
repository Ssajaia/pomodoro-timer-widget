from __future__ import annotations
import tkinter as tk
from tkinter import messagebox
from typing import Callable

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
        self.bind("<Return>", lambda e: self._save())
        self.bind("<Escape>", lambda e: self.destroy())

        self._build_ui()
        self._center(parent)

    def _center(self, parent: tk.Tk) -> None:
        self.update_idletasks()
        px = parent.winfo_x() + parent.winfo_width() // 2
        py = parent.winfo_y() + parent.winfo_height() // 2
        self.geometry(f"+{px - self.winfo_width() // 2}+{py - self.winfo_height() // 2}")

    def _build_ui(self) -> None:
        t = self._theme
        c = self._config

        canvas = tk.Canvas(self, bg=t.bg, highlightthickness=0, width=420)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=t.bg)
        inner_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(inner_id, width=canvas.winfo_width())

        inner.bind("<Configure>", on_configure)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(inner_id, width=e.width))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        pad = dict(padx=20, pady=6)
        lbl = dict(bg=t.bg, fg=t.fg, font=("Segoe UI", 10))
        entry_opts = dict(
            bg=t.input_bg, fg=t.input_fg,
            insertbackground=t.fg,
            relief="flat",
            highlightthickness=1,
            highlightcolor=t.accent,
            highlightbackground=t.border,
            font=("Segoe UI", 10),
            width=10,
        )

        def section(text: str) -> None:
            tk.Frame(inner, bg=t.border, height=1).pack(fill="x", padx=20, pady=(16, 0))
            tk.Label(inner, text=text, bg=t.bg, fg=t.accent,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=20, pady=(6, 2))

        def row(parent, label: str, widget_fn) -> None:
            f = tk.Frame(parent, bg=t.bg)
            f.pack(fill="x", **pad)
            tk.Label(f, text=label, **lbl).pack(side="left")
            widget_fn(f)

        def entry_row(label: str, var: tk.StringVar, entry_kw: dict = {}) -> None:
            def make(f):
                e = tk.Entry(f, textvariable=var, **{**entry_opts, **entry_kw})
                e.pack(side="right")
                e.bind("<Return>", lambda ev: self._save())
            row(inner, label, make)

        def check_row(label: str, var: tk.BooleanVar) -> None:
            f = tk.Frame(inner, bg=t.bg)
            f.pack(fill="x", padx=20, pady=4)
            tk.Checkbutton(
                f, text=label, variable=var,
                bg=t.bg, fg=t.fg, selectcolor=t.bg_secondary,
                activebackground=t.bg, activeforeground=t.fg,
                relief="flat", bd=0, highlightthickness=0,
                font=("Segoe UI", 10),
            ).pack(side="left")

        def dropdown_row(label: str, var: tk.StringVar, *options) -> None:
            def make(f):
                cb = tk.OptionMenu(f, var, *options)
                cb.configure(
                    bg=t.input_bg, fg=t.input_fg,
                    activebackground=t.bg_secondary, activeforeground=t.fg,
                    relief="flat", bd=0, highlightthickness=0,
                    font=("Segoe UI", 10), width=12,
                )
                cb["menu"].configure(bg=t.input_bg, fg=t.input_fg, font=("Segoe UI", 10))
                cb.pack(side="right")
            row(inner, label, make)

        def scale_row(label: str, var: tk.DoubleVar, from_: float, to: float, resolution: float) -> None:
            def make(f):
                tk.Scale(
                    f, from_=from_, to=to, resolution=resolution,
                    variable=var, orient="horizontal",
                    bg=t.bg, fg=t.fg, troughcolor=t.bg_secondary,
                    highlightthickness=0, bd=0, length=140,
                ).pack(side="right")
            row(inner, label, make)

        tk.Label(inner, text="Settings", bg=t.bg, fg=t.fg,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=20, pady=(16, 0))

        section("Timer Durations")
        self._focus_var = tk.StringVar(value=str(c.timer.focus_minutes))
        self._short_var = tk.StringVar(value=str(c.timer.short_break_minutes))
        self._long_var = tk.StringVar(value=str(c.timer.long_break_minutes))
        self._sessions_var = tk.StringVar(value=str(c.timer.sessions_before_long_break))
        entry_row("Focus (min)", self._focus_var)
        entry_row("Short Break (min)", self._short_var)
        entry_row("Long Break (min)", self._long_var)
        entry_row("Sessions before Long Break", self._sessions_var)

        section("Auto-start")
        self._auto_break_var = tk.BooleanVar(value=c.timer.auto_start_breaks)
        self._auto_focus_var = tk.BooleanVar(value=c.timer.auto_start_focus)
        check_row("Auto-start breaks", self._auto_break_var)
        check_row("Auto-start focus sessions", self._auto_focus_var)

        section("Appearance")
        self._theme_var = tk.StringVar(value=c.theme)
        self._opacity_var = tk.DoubleVar(value=c.window.opacity)
        self._close_tray_var = tk.BooleanVar(value=c.window.close_to_tray)
        dropdown_row("Theme", self._theme_var, "dark", "light", "obsidianite")
        scale_row("Opacity", self._opacity_var, 0.3, 1.0, 0.05)
        check_row("Close button minimizes to tray", self._close_tray_var)

        section("Sound")
        self._sound_var = tk.BooleanVar(value=c.notifications.sound_enabled)
        check_row("Play sound when session ends", self._sound_var)

        tk.Frame(inner, bg=t.border, height=1).pack(fill="x", padx=20, pady=(16, 0))

        btn_row = tk.Frame(inner, bg=t.bg)
        btn_row.pack(fill="x", padx=20, pady=16)

        tk.Button(
            btn_row, text="Cancel", command=self.destroy,
            bg=t.bg_secondary, fg=t.fg_secondary, relief="flat",
            font=("Segoe UI", 10), padx=20, pady=8,
            activebackground=t.border, activeforeground=t.fg, cursor="hand2",
        ).pack(side="right", padx=(8, 0))

        tk.Button(
            btn_row, text="Save", command=self._save,
            bg=t.accent, fg=t.button_fg, relief="flat",
            font=("Segoe UI", 10, "bold"), padx=20, pady=8,
            activebackground=t.accent_hover, activeforeground=t.button_fg, cursor="hand2",
        ).pack(side="right")

        self.update_idletasks()
        h = min(520, inner.winfo_reqheight() + 20)
        self.geometry(f"440x{h}")

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
        self._config.notifications.sound_enabled = self._sound_var.get()

        self._on_save(self._config)
        self.destroy()