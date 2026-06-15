# Pomodoro Timer

A lightweight, always-on-top Pomodoro timer for Windows. Floating widget style with system tray support, dark/light themes, native notifications, and persistent statistics.

## Features

- 25/5/15 min Pomodoro cycle (fully configurable)
- Borderless floating widget, draggable
- Always on top
- Minimize to system tray
- Dark and light themes with per-session phase colors
- Progress ring visualization
- Native Windows toast notifications + sound
- Session and daily statistics
- Persistent settings and stats across launches
- Single-command build to standalone `.exe`

## Requirements

- Python 3.13+
- Windows 10/11

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Build

```bash
pyinstaller pomodoro.spec
```

Output: `dist/PomodoroTimer.exe`

## Usage

| Action | How |
|---|---|
| Move window | Drag title bar |
| Toggle compact mode | Double-click title bar |
| Open settings | ⚙ button |
| Minimize to tray | ⊟ button or close (if configured) |
| Restore from tray | Double-click tray icon |
| Quit | Tray icon → Quit |

## Data Storage

Settings and stats are stored in `%APPDATA%\PomodoroTimer\`.
