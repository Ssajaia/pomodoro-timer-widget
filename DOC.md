# DOC

## Project Tree

```
pomodoro/
├── assets/
│   ├── icon.ico
│   └── icon.png
├── core/
│   ├── __init__.py
│   ├── config.py
│   └── timer.py
├── notifications/
│   ├── __init__.py
│   └── manager.py
├── ui/
│   ├── __init__.py
│   ├── app_window.py
│   ├── progress_ring.py
│   ├── settings_dialog.py
│   ├── themes.py
│   └── tray.py
├── main.py
├── pomodoro.spec
├── requirements.txt
├── README.md
└── DOC.md
```

## Build Command

```bash
pyinstaller pomodoro.spec
```

## Run Command

```bash
python main.py
```
