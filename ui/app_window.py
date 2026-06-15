from __future__ import annotations
import os
import sys
import tkinter as tk
from typing import Optional

from core.config import AppConfig, Stats
from core.timer import Phase, PomodoroTimer, TimerState
from ui.progress_ring import ProgressRing
from ui.settings_dialog import SettingsDialog
from ui.themes import Theme, get_theme
from ui.tray import TrayIcon


def _icon_path() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", "icon.ico")


def _png_path() -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "assets", "icon.png")


class AppWindow:
    def __init__(self) -> None:
        self._config = AppConfig.load()
        self._stats = Stats.load()
        self._theme: Theme = get_theme(self._config.theme)
        self._compact: bool = self._config.window.compact
        self._focus_mode: bool = False

        self._root = tk.Tk()
        self._root.withdraw()

        self._setup_dpi()
        self._setup_window()
        self._setup_timer()
        self._build_ui()
        self._setup_tray()
        self._restore_position()
        self._root.deiconify()

    def _setup_dpi(self) -> None:
        if sys.platform == "win32":
            try:
                from ctypes import windll
                windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    windll.user32.SetProcessDPIAware()
                except Exception:
                    pass

    def _setup_window(self) -> None:
        r = self._root
        t = self._theme
        r.configure(bg=t.bg)
        r.overrideredirect(True)
        r.wm_attributes("-topmost", True)
        r.wm_attributes("-alpha", self._config.window.opacity)
        w = self._config.window.width
        h = self._config.window.height if not self._compact else 140
        r.geometry(f"{w}x{h}")
        try:
            r.iconbitmap(_icon_path())
        except Exception:
            pass
        r.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_timer(self) -> None:
        tc = self._config.timer
        self._timer = PomodoroTimer(
            focus_minutes=tc.focus_minutes,
            short_break_minutes=tc.short_break_minutes,
            long_break_minutes=tc.long_break_minutes,
            sessions_before_long=tc.sessions_before_long_break,
            on_tick=self._on_tick,
            on_phase_change=self._on_phase_change,
            on_session_complete=self._on_session_complete,
        )
        self._timer.attach_tk(self._root)

    def _build_ui(self) -> None:
        t = self._theme
        r = self._root

        for child in r.winfo_children():
            child.destroy()

        if self._focus_mode:
            self._build_focus_mode()
            return

        self._title_bar = tk.Frame(r, bg=t.title_bar_bg, height=36)
        self._title_bar.pack(fill="x")
        self._title_bar.pack_propagate(False)
        self._title_bar.bind("<ButtonPress-1>", self._drag_start)
        self._title_bar.bind("<B1-Motion>", self._drag_motion)

        self._lbl_title = tk.Label(
            self._title_bar, text="🍅 Pomodoro",
            bg=t.title_bar_bg, fg=t.title_bar_fg,
            font=("Segoe UI", 10, "bold"), padx=12,
        )
        self._lbl_title.pack(side="left")
        self._lbl_title.bind("<ButtonPress-1>", self._drag_start)
        self._lbl_title.bind("<B1-Motion>", self._drag_motion)

        btn_opts = dict(
            bg=t.title_bar_bg, relief="flat", bd=0,
            activebackground=t.bg_secondary, cursor="hand2",
            font=("Segoe UI", 11),
        )

        self._btn_settings = tk.Button(
            self._title_bar, text="⚙", fg=t.fg_secondary,
            activeforeground=t.fg, command=self._open_settings, **btn_opts
        )
        self._btn_settings.pack(side="right", padx=(0, 2))

        self._btn_focus_mode = tk.Button(
            self._title_bar, text="◎", fg=t.fg_secondary,
            activeforeground=t.fg, command=self._enter_focus_mode, **btn_opts
        )
        self._btn_focus_mode.pack(side="right")

        self._btn_minimize = tk.Button(
            self._title_bar, text="⊟", fg=t.fg_secondary,
            activeforeground=t.fg, command=self._minimize, **btn_opts
        )
        self._btn_minimize.pack(side="right")

        self._btn_close = tk.Button(
            self._title_bar, text="✕", fg=t.fg_secondary,
            activeforeground=t.danger, command=self._on_close, **btn_opts
        )
        self._btn_close.pack(side="right")

        self._content = tk.Frame(r, bg=t.bg)
        self._content.pack(fill="both", expand=True)

        self._build_main_content()

    def _build_focus_mode(self) -> None:
        t = self._theme
        r = self._root

        outer = tk.Frame(r, bg=t.bg)
        outer.pack(fill="both", expand=True)
        outer.bind("<ButtonPress-1>", self._drag_start)
        outer.bind("<B1-Motion>", self._drag_motion)
        outer.bind("<Double-Button-1>", self._exit_focus_mode)

        ring_size = 140
        ring_frame = tk.Frame(outer, bg=t.bg)
        ring_frame.pack(expand=True)
        ring_frame.bind("<ButtonPress-1>", self._drag_start)
        ring_frame.bind("<B1-Motion>", self._drag_motion)
        ring_frame.bind("<Double-Button-1>", self._exit_focus_mode)

        self._ring = ProgressRing(ring_frame, size=ring_size, theme=t)
        self._ring.pack()
        self._ring.bind("<ButtonPress-1>", self._drag_start)
        self._ring.bind("<B1-Motion>", self._drag_motion)
        self._ring.bind("<Double-Button-1>", self._exit_focus_mode)

        remaining = self._timer.remaining
        total = self._timer.total_seconds
        progress = remaining / total if total > 0 else 1.0
        self._ring.set_progress(progress, color=self._phase_color())

        self._time_label = tk.Label(
            ring_frame, text=self._format_time(remaining),
            bg=t.bg, fg=t.fg,
            font=("Consolas", 20, "bold"),
        )
        self._time_label.bind("<ButtonPress-1>", self._drag_start)
        self._time_label.bind("<B1-Motion>", self._drag_motion)
        self._time_label.bind("<Double-Button-1>", self._exit_focus_mode)

        self._ring.after(10, lambda: self._time_label.place(
            x=ring_size // 2, y=ring_size // 2, anchor="center"
        ))

        self._root.geometry(f"160x160+{self._root.winfo_x()}+{self._root.winfo_y()}")
        self._root.wm_attributes("-alpha", max(0.3, self._config.window.opacity - 0.1))

    def _enter_focus_mode(self) -> None:
        self._focus_mode = True
        self._build_ui()

    def _exit_focus_mode(self, event=None) -> None:
        self._focus_mode = False
        self._root.wm_attributes("-alpha", self._config.window.opacity)
        w = self._config.window.width
        h = self._config.window.height
        self._root.geometry(f"{w}x{h}+{self._root.winfo_x()}+{self._root.winfo_y()}")
        self._build_ui()

    def _build_main_content(self) -> None:
        t = self._theme
        c = self._content

        for w in c.winfo_children():
            w.destroy()

        self._phase_label = tk.Label(
            c, text=self._phase_text(), fg=self._phase_color(),
            bg=t.bg, font=("Segoe UI", 10, "bold"),
        )
        self._phase_label.pack(pady=(10, 0))

        ring_size = 80 if self._compact else 150
        self._ring_frame = tk.Frame(c, bg=t.bg)
        self._ring_frame.pack(pady=(6, 0))

        self._ring = ProgressRing(self._ring_frame, size=ring_size, theme=t)
        self._ring.pack()

        remaining = self._timer.remaining
        total = self._timer.total_seconds
        progress = remaining / total if total > 0 else 1.0
        self._ring.set_progress(progress, color=self._phase_color())

        self._time_label = tk.Label(
            self._ring_frame, text=self._format_time(remaining),
            bg=t.bg, fg=t.fg,
            font=("Consolas", 20 if not self._compact else 13, "bold"),
        )
        self._time_label.place(relx=0.5, rely=0.5, anchor="center")
        self._ring.after(10, self._sync_time_label_position)

        if not self._compact:
            self._build_duration_row(c, t)
            self._build_stats(c, t)
            self._build_buttons(c, t)

    def _build_duration_row(self, parent: tk.Frame, t: Theme) -> None:
        frame = tk.Frame(parent, bg=t.bg)
        frame.pack(pady=(8, 0))

        entry_opts = dict(
            bg=t.input_bg, fg=t.input_fg,
            insertbackground=t.fg,
            relief="flat",
            highlightthickness=1,
            highlightcolor=t.accent,
            highlightbackground=t.border,
            font=("Segoe UI", 9),
            width=3,
            justify="center",
        )
        label_opts = dict(bg=t.bg, fg=t.fg_secondary, font=("Segoe UI", 8))

        def make_field(parent, label_text: str, value: int):
            col = tk.Frame(parent, bg=t.bg)
            col.pack(side="left", padx=5)
            tk.Label(col, text=label_text, **label_opts).pack()
            var = tk.StringVar(value=str(value))
            entry = tk.Entry(col, textvariable=var, **entry_opts)
            entry.pack()
            return var

        self._dur_focus_var = make_field(frame, "Focus", self._config.timer.focus_minutes)
        self._dur_short_var = make_field(frame, "Short", self._config.timer.short_break_minutes)
        self._dur_long_var = make_field(frame, "Long", self._config.timer.long_break_minutes)

        apply_btn = tk.Button(
            frame, text="✓",
            bg=t.accent, fg=t.button_fg,
            activebackground=t.accent_hover, activeforeground=t.button_fg,
            relief="flat", font=("Segoe UI", 10, "bold"),
            padx=6, pady=2, cursor="hand2",
            command=self._apply_inline_durations,
        )
        apply_btn.pack(side="left", padx=(6, 0), pady=(12, 0))

    def _apply_inline_durations(self) -> None:
        try:
            focus = int(self._dur_focus_var.get())
            short = int(self._dur_short_var.get())
            long_ = int(self._dur_long_var.get())
        except (ValueError, AttributeError):
            return
        if not (1 <= focus <= 120 and 1 <= short <= 60 and 1 <= long_ <= 120):
            return
        self._config.timer.focus_minutes = focus
        self._config.timer.short_break_minutes = short
        self._config.timer.long_break_minutes = long_
        self._config.save()
        self._timer.update_durations(
            focus, short, long_,
            self._config.timer.sessions_before_long_break,
        )
        self._on_tick(self._timer.remaining)

    def _sync_time_label_position(self) -> None:
        try:
            s = self._ring.winfo_width()
            self._time_label.place(x=s // 2, y=s // 2, anchor="center")
        except Exception:
            pass

    def _build_stats(self, parent: tk.Frame, t: Theme) -> None:
        stats_frame = tk.Frame(parent, bg=t.bg)
        stats_frame.pack(pady=(6, 0))

        self._session_label = tk.Label(
            stats_frame,
            text=f"Session {self._timer.session_count + 1}  •  Today: {self._stats.today_count()} 🍅",
            bg=t.bg, fg=t.fg_secondary, font=("Segoe UI", 9),
        )
        self._session_label.pack()

        self._total_label = tk.Label(
            stats_frame,
            text=f"Total: {self._stats.total_pomodoros} pomodoros",
            bg=t.bg, fg=t.fg_secondary, font=("Segoe UI", 9),
        )
        self._total_label.pack()

    def _build_buttons(self, parent: tk.Frame, t: Theme) -> None:
        btn_frame = tk.Frame(parent, bg=t.bg)
        btn_frame.pack(pady=(10, 0))

        btn_row1 = tk.Frame(btn_frame, bg=t.bg)
        btn_row1.pack()

        self._btn_start = tk.Button(
            btn_row1, text="▶ Start",
            bg=t.accent, fg=t.button_fg,
            activebackground=t.accent_hover, activeforeground=t.button_fg,
            relief="flat", font=("Segoe UI", 10, "bold"),
            padx=14, pady=6, cursor="hand2",
            command=self._on_start_pause,
        )
        self._btn_start.pack(side="left", padx=4)

        self._btn_reset = tk.Button(
            btn_row1, text="↺ Reset",
            bg=t.bg_secondary, fg=t.fg,
            activebackground=t.border, activeforeground=t.fg,
            relief="flat", font=("Segoe UI", 10),
            padx=14, pady=6, cursor="hand2",
            command=self._on_reset,
        )
        self._btn_reset.pack(side="left", padx=4)

        btn_row2 = tk.Frame(btn_frame, bg=t.bg)
        btn_row2.pack(pady=(6, 0))

        self._btn_skip = tk.Button(
            btn_row2, text="⏭ Skip",
            bg=t.bg_tertiary, fg=t.fg,
            activebackground=t.border, activeforeground=t.fg,
            relief="flat", font=("Segoe UI", 9),
            padx=12, pady=4, cursor="hand2",
            command=self._on_skip,
        )
        self._btn_skip.pack()

        self._update_buttons()

    def _phase_text(self) -> str:
        labels = {
            Phase.FOCUS: "FOCUS",
            Phase.SHORT_BREAK: "SHORT BREAK",
            Phase.LONG_BREAK: "LONG BREAK",
        }
        return labels[self._timer.phase]

    def _phase_color(self) -> str:
        t = self._theme
        colors = {
            Phase.FOCUS: t.accent,
            Phase.SHORT_BREAK: t.accent_break,
            Phase.LONG_BREAK: t.accent_long,
        }
        return colors[self._timer.phase]

    @staticmethod
    def _format_time(seconds: int) -> str:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _on_tick(self, remaining: int) -> None:
        total = self._timer.total_seconds
        progress = remaining / total if total > 0 else 0.0
        self._ring.set_progress(progress, color=self._phase_color())
        try:
            self._time_label.configure(text=self._format_time(remaining))
        except tk.TclError:
            pass
        self._update_tray_tooltip(remaining)

    def _on_phase_change(self, phase: Phase) -> None:
        try:
            self._phase_label.configure(text=self._phase_text(), fg=self._phase_color())
            self._ring.set_progress(1.0, color=self._phase_color())
            self._time_label.configure(text=self._format_time(self._timer.remaining))
            self._update_buttons()
            auto = (
                self._config.timer.auto_start_breaks and phase != Phase.FOCUS
            ) or (
                self._config.timer.auto_start_focus and phase == Phase.FOCUS
            )
            if auto and self._timer.state == TimerState.IDLE:
                self._timer.start()
        except (tk.TclError, AttributeError):
            pass

    def _on_session_complete(self, completed_phase: Phase) -> None:
        if completed_phase == Phase.FOCUS:
            self._stats.increment(self._config.timer.focus_minutes)
            self._stats.save()
            self._update_stats_labels()
        self._update_buttons()

    def _update_stats_labels(self) -> None:
        try:
            self._session_label.configure(
                text=f"Session {self._timer.session_count + 1}  •  Today: {self._stats.today_count()} 🍅"
            )
            self._total_label.configure(
                text=f"Total: {self._stats.total_pomodoros} pomodoros"
            )
        except (tk.TclError, AttributeError):
            pass

    def _update_buttons(self) -> None:
        try:
            t = self._theme
            state = self._timer.state
            if state == TimerState.RUNNING:
                self._btn_start.configure(text="⏸ Pause", bg=t.bg_secondary, fg=t.fg)
            elif state == TimerState.PAUSED:
                self._btn_start.configure(text="▶ Resume", bg=t.accent, fg=t.button_fg)
            else:
                self._btn_start.configure(text="▶ Start", bg=t.accent, fg=t.button_fg)
        except (tk.TclError, AttributeError):
            pass

    def _on_start_pause(self) -> None:
        state = self._timer.state
        if state == TimerState.IDLE:
            self._timer.start()
        elif state == TimerState.RUNNING:
            self._timer.pause()
        else:
            self._timer.resume()
        self._update_buttons()

    def _on_reset(self) -> None:
        self._timer.reset()
        self._ring.set_progress(1.0, color=self._phase_color())
        self._time_label.configure(text=self._format_time(self._timer.remaining))
        self._update_buttons()

    def _on_skip(self) -> None:
        self._timer.skip()
        self._update_buttons()

    def _open_settings(self) -> None:
        def on_save(cfg: AppConfig) -> None:
            self._config = cfg
            self._config.save()
            self._theme = get_theme(cfg.theme)
            self._apply_theme()
            self._timer.update_durations(
                cfg.timer.focus_minutes,
                cfg.timer.short_break_minutes,
                cfg.timer.long_break_minutes,
                cfg.timer.sessions_before_long_break,
            )
            self._root.wm_attributes("-alpha", cfg.window.opacity)
            self._on_tick(self._timer.remaining)

        SettingsDialog(self._root, self._config, self._theme, on_save)

    def _apply_theme(self) -> None:
        self._root.configure(bg=self._theme.bg)
        self._build_ui()

    def _restore_position(self) -> None:
        w = self._config.window
        if w.x is not None and w.y is not None:
            self._root.geometry(f"{w.width}x{w.height}+{w.x}+{w.y}")
        else:
            self._center_on_screen()

    def _center_on_screen(self) -> None:
        self._root.update_idletasks()
        sw = self._root.winfo_screenwidth()
        sh = self._root.winfo_screenheight()
        w = self._config.window.width
        h = self._config.window.height
        self._root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _drag_start(self, event: tk.Event) -> None:
        self._drag_x = event.x_root - self._root.winfo_x()
        self._drag_y = event.y_root - self._root.winfo_y()

    def _drag_motion(self, event: tk.Event) -> None:
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self._root.geometry(f"+{x}+{y}")

    def _save_position(self) -> None:
        if not self._focus_mode:
            self._config.window.x = self._root.winfo_x()
            self._config.window.y = self._root.winfo_y()
            self._config.window.width = self._root.winfo_width()
            self._config.window.height = self._root.winfo_height()
        self._config.save()

    def _minimize(self) -> None:
        self._save_position()
        self._root.withdraw()
        self._tray.start()

    def _on_close(self) -> None:
        self._save_position()
        if self._config.window.close_to_tray:
            self._minimize()
        else:
            self._quit()

    def _restore_from_tray(self) -> None:
        self._root.after(0, self._do_restore)

    def _do_restore(self) -> None:
        self._root.deiconify()
        self._root.lift()
        self._root.wm_attributes("-topmost", True)

    def _quit(self) -> None:
        self._save_position()
        self._stats.save()
        self._tray.stop()
        self._root.quit()
        self._root.destroy()

    def _setup_tray(self) -> None:
        self._tray = TrayIcon(
            icon_path=_png_path(),
            tooltip="Pomodoro Timer",
            on_restore=self._restore_from_tray,
            on_quit=self._quit,
        )

    def _update_tray_tooltip(self, remaining: int) -> None:
        self._tray.update_tooltip(f"Pomodoro — {self._phase_text()} {self._format_time(remaining)}")

    def run(self) -> None:
        self._root.mainloop()