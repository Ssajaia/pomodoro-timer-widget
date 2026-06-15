from __future__ import annotations
import time
from enum import Enum
from typing import Callable, Optional


class Phase(Enum):
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class TimerState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"


class PomodoroTimer:
    def __init__(
        self,
        focus_minutes: int = 25,
        short_break_minutes: int = 5,
        long_break_minutes: int = 15,
        sessions_before_long: int = 4,
        on_tick: Optional[Callable[[int], None]] = None,
        on_phase_change: Optional[Callable[[Phase], None]] = None,
        on_session_complete: Optional[Callable[[Phase], None]] = None,
    ) -> None:
        self.focus_minutes = focus_minutes
        self.short_break_minutes = short_break_minutes
        self.long_break_minutes = long_break_minutes
        self.sessions_before_long = sessions_before_long
        self.on_tick = on_tick
        self.on_phase_change = on_phase_change
        self.on_session_complete = on_session_complete

        self.phase: Phase = Phase.FOCUS
        self.state: TimerState = TimerState.IDLE
        self.session_count: int = 0
        self.completed_cycles: int = 0

        self._remaining: int = focus_minutes * 60
        self._start_wall: float = 0.0
        self._elapsed_at_pause: int = 0
        self._after_id: Optional[str] = None
        self._tk_root = None

    def attach_tk(self, root) -> None:
        self._tk_root = root

    def _phase_duration(self) -> int:
        if self.phase == Phase.FOCUS:
            return self.focus_minutes * 60
        elif self.phase == Phase.SHORT_BREAK:
            return self.short_break_minutes * 60
        else:
            return self.long_break_minutes * 60

    @property
    def remaining(self) -> int:
        if self.state == TimerState.RUNNING:
            elapsed = int(time.monotonic() - self._start_wall) + self._elapsed_at_pause
            remaining = max(0, self._phase_duration() - elapsed)
            return remaining
        return self._remaining

    @property
    def total_seconds(self) -> int:
        return self._phase_duration()

    def start(self) -> None:
        if self.state == TimerState.RUNNING:
            return
        self._elapsed_at_pause = self._phase_duration() - self._remaining
        self._start_wall = time.monotonic()
        self.state = TimerState.RUNNING
        self._schedule_tick()
        if self.on_phase_change:
            self.on_phase_change(self.phase)

    def pause(self) -> None:
        if self.state != TimerState.RUNNING:
            return
        self._remaining = self.remaining
        self._elapsed_at_pause = self._phase_duration() - self._remaining
        self.state = TimerState.PAUSED
        self._cancel_tick()

    def resume(self) -> None:
        if self.state != TimerState.PAUSED:
            return
        self._start_wall = time.monotonic()
        self.state = TimerState.RUNNING
        self._schedule_tick()

    def reset(self) -> None:
        self._cancel_tick()
        self.state = TimerState.IDLE
        self._remaining = self._phase_duration()
        self._elapsed_at_pause = 0
        if self.on_tick:
            self.on_tick(self._remaining)

    def skip(self) -> None:
        self._cancel_tick()
        completed_phase = self.phase
        self._advance_phase()
        if self.on_session_complete:
            self.on_session_complete(completed_phase)

    def _advance_phase(self) -> None:
        if self.phase == Phase.FOCUS:
            self.session_count += 1
            if self.session_count % self.sessions_before_long == 0:
                self.completed_cycles += 1
                self.phase = Phase.LONG_BREAK
            else:
                self.phase = Phase.SHORT_BREAK
        else:
            self.phase = Phase.FOCUS

        self.state = TimerState.IDLE
        self._remaining = self._phase_duration()
        self._elapsed_at_pause = 0

        if self.on_phase_change:
            self.on_phase_change(self.phase)
        if self.on_tick:
            self.on_tick(self._remaining)

    def update_durations(
        self,
        focus_minutes: int,
        short_break_minutes: int,
        long_break_minutes: int,
        sessions_before_long: int,
    ) -> None:
        was_idle = self.state == TimerState.IDLE
        self.focus_minutes = focus_minutes
        self.short_break_minutes = short_break_minutes
        self.long_break_minutes = long_break_minutes
        self.sessions_before_long = sessions_before_long
        if was_idle:
            self._remaining = self._phase_duration()
            if self.on_tick:
                self.on_tick(self._remaining)

    def _schedule_tick(self) -> None:
        if self._tk_root is None:
            return
        self._after_id = self._tk_root.after(250, self._tick)

    def _cancel_tick(self) -> None:
        if self._tk_root and self._after_id:
            try:
                self._tk_root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None

    def _tick(self) -> None:
        if self.state != TimerState.RUNNING:
            return
        remaining = self.remaining
        if self.on_tick:
            self.on_tick(remaining)
        if remaining <= 0:
            completed_phase = self.phase
            self._advance_phase()
            if self.on_session_complete:
                self.on_session_complete(completed_phase)
            return
        self._schedule_tick()
