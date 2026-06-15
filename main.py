import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.app_window import AppWindow


def main() -> None:
    app = AppWindow()
    app.run()


if __name__ == "__main__":
    main()
