import threading
import pystray
from PIL import Image
from pathlib import Path
from screeninfo import get_monitors

from settings import settings

ROOT_DIR = Path(__file__).resolve().parent


primary_monitor = get_monitors()[0]
screen_width = primary_monitor.width
screen_height = primary_monitor.height

tray_app_width_percentage = settings.tray_app.width_percentage
tray_app_height_percentage = settings.tray_app.height_percentage
collapsed_win_width = int(screen_width * (tray_app_width_percentage / 100))
collapsed_win_height = int(screen_height * (tray_app_height_percentage / 100))

expanded_tray_app_width_percentage = settings.tray_app.expanded_width_percentage
expanded_tray_app_height_percentage = settings.tray_app.expanded_height_percentage

expanded_win_width = int(screen_width * (expanded_tray_app_width_percentage / 100))
expanded_win_height = int(screen_height * (expanded_tray_app_height_percentage / 100))


class WindowAPI:
    def __init__(self, window):
        self.window = window
        self.icon = None
        self._expanded = False

    def on_blur(self):
        self.window.hide()

    def close_app(self):
        if self.icon is not None:
            self.icon.stop()
        self.window.destroy()

    def minimise(self):
        self.window.minimize()

    def toggle_expand(self):
        if self._expanded:
            self.window.resize(expanded_win_width, expanded_win_height)
        else:
            self.window.resize(collapsed_win_width, collapsed_win_height)
        self._expanded = not self._expanded


def mark_as_tray_app(window):
    window.evaluate_js("localStorage.setItem('trayApp', 'true')")


def _toggle_window(window):
    if window.hidden:
        window.show()
    else:
        window.hide()


def _exit_app(icon, window):
    icon.stop()
    window.destroy()


def start_tray(window, api=None):
    icon_path = ROOT_DIR / "assets" / "kodo_icon.ico"
    image = Image.open(icon_path)

    menu = pystray.Menu(
        pystray.MenuItem("Open Kodo", lambda: _toggle_window(window), default=True),
        pystray.MenuItem("Exit", lambda: _exit_app(icon, window)),
    )
    icon = pystray.Icon("kodo", image, "Kodo", menu)
    if api is not None:
        api.icon = icon
    threading.Thread(target=icon.run, daemon=True).start()
