import threading
import pystray
from PIL import Image
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent


class WindowAPI:
    def __init__(self, window):
        self.window = window

    def on_blur(self):
        self.window.hide()


def _toggle_window(window):
    if window.hidden:
        window.show()
    else:
        window.hide()


def _exit_app(icon, window):
    icon.stop()
    window.destroy()


def start_tray(window):
    icon_path = ROOT_DIR / "assets" / "kodo_icon.ico"
    image = Image.open(icon_path)

    menu = pystray.Menu(
        pystray.MenuItem("Open Kodo", lambda: _toggle_window(window), default=True),
        pystray.MenuItem("Exit", lambda: _exit_app(icon, window)),
    )
    icon = pystray.Icon("kodo", image, "Kodo", menu)
    threading.Thread(target=icon.run, daemon=True).start()
