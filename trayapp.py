import threading
import time
import pystray
from PIL import Image
from pathlib import Path
from screeninfo import get_monitors

from settings import settings
from server.run_tracker import teardown_all

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

RESIZE_ANIMATION_DURATION_S = 0.28
RESIZE_ANIMATION_FPS = 60


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


class WindowAPI:
    def __init__(self, window):
        self.window = window
        self.icon = None
        self._expanded = False
        self._pinned = False
        self._resize_token = 0

    def on_blur(self):
        if self._pinned:
            return
        self.window.hide()

    def toggle_pin(self):
        self._pinned = not self._pinned
        return self._pinned

    def close_app(self):
        if self.icon is not None:
            self.icon.stop()
        self.window.destroy()
        teardown_all()

    def minimise(self):
        self.window.minimize()

    def toggle_expand(self):
        if self._expanded:
            target_width, target_height = collapsed_win_width, collapsed_win_height
        else:
            target_width, target_height = expanded_win_width, expanded_win_height
        self._expanded = not self._expanded

        self._resize_token += 1
        token = self._resize_token
        threading.Thread(
            target=self._animate_resize,
            args=(target_width, target_height, token),
            daemon=True,
        ).start()

    def _animate_resize(self, target_width, target_height, token):
        start_height = self.window.height
        start_width = self.window.width
        steps = max(1, int(RESIZE_ANIMATION_DURATION_S * RESIZE_ANIMATION_FPS))
        step_delay = RESIZE_ANIMATION_DURATION_S / steps

        for i in range(1, steps + 1):
            if token != self._resize_token:
                return

            eased = _ease_out_cubic(i / steps)
            width = int(start_width + (target_width - start_width) * eased)
            height = int(start_height + (target_height - start_height) * eased)
            self.window.resize(width, height)
            time.sleep(step_delay)


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
    teardown_all()


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
