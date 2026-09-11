import os
import subprocess
import sys
from pathlib import Path
import sys
import bootstrapper

from utils import check_layer
from utils import toaster

from settings import settings


from utils.globals import (
    API_BIND_TO_ALL_IPS,
    API_PORT,
    WEB_PORT,
    TRAY_APP_HEIGHT_PERCENTAGE,
    TRAY_APP_WIDTH_PERCENTAGE,
    TRAY_APP_X_POSITION_PERCENTAGE,
    TRAY_APP_Y_POSITION_PERCENTAGE,
)

HOST = "127.0.0.1"
if API_BIND_TO_ALL_IPS:
    HOST = "0.0.0.0"

ROOT_DIR = Path(__file__).resolve().parent
os.chdir(ROOT_DIR)


def _venv_python() -> Path:
    return ROOT_DIR / "venv" / "Scripts" / "python.exe"


def _run_under_venv():
    venv_python = _venv_python()
    if not venv_python.exists():
        return False
    if os.path.abspath(sys.executable) == os.path.abspath(str(venv_python)):
        return False

    sys.exit(subprocess.call([str(venv_python)] + sys.argv))


if __name__ == "__main__":
    if not Path(ROOT_DIR / "initialised.txt").exists():
        from setup import KodoSetup

        setup = KodoSetup()
        setup.check_system_compatibility()
        setup.run_setup_sequence()

    _run_under_venv()

    bootstrapper.run_config_guard()
    if check_layer("mcps"):
        bootstrapper.setup_mcps()

    toaster.update(
        "Kodo Toast Notifications",
        "Kodo will post its status throughout all runs in your Windows Action Center",
    )

    if "-t" in sys.argv:
        arguments = sys.argv.copy()

        task_flag_position = arguments.index("-t")
        task = " ".join(arguments[task_flag_position + 1 :])

        from orchestrator import run_externally

        run_externally(task=task)
        sys.exit(0)

    else:
        import uvicorn
        import webview
        from trayapp import start_tray, WindowAPI, mark_as_tray_app

        def _inject_blur_listener(window):
            window.evaluate_js("""
                window.addEventListener('blur', () => {
                    window.pywebview.api.on_blur();
                });
            """)

        # Deprecate the built in Web UI for the other one at KodoFrontend.
        web_port = settings.tray_app.web_ui_port
        webview_port = web_port if web_port else API_PORT  # The port used by the tray

        # This change is being made because the built in WebUI will be deprecated soon.

        from screeninfo import get_monitors

        primary_monitor = get_monitors()[0]
        screen_width = primary_monitor.width
        screen_height = primary_monitor.height

        tray_app_width_percentage = settings.tray_app.width_percentage
        tray_app_height_percentage = settings.tray_app.height_percentage
        tray_app_x_position_percentage = settings.tray_app.x_position_percentage
        tray_app_y_position_percentage = settings.tray_app.y_position_percentage

        win_width = int(screen_width * (tray_app_width_percentage / 100))
        win_height = int(screen_height * (tray_app_height_percentage / 100))

        win = webview.create_window(
            "Kodo",
            f"http://localhost:{webview_port}",
            frameless=True,
            width=win_width,
            height=win_height,
            x=int((screen_width - win_width) * (tray_app_x_position_percentage / 100)),
            y=int(
                (screen_height - win_height) * (tray_app_y_position_percentage / 100)
            ),
            hidden=True,
            resizable=True,
            easy_drag=True,
        )

        window_api = WindowAPI(win)
        win.expose(  # type: ignore
            window_api.on_blur,
            window_api.close_app,
            window_api.minimise,
            window_api.toggle_expand,
        )
        win.events.loaded += lambda: _inject_blur_listener(win)  # type: ignore
        win.events.loaded += lambda: mark_as_tray_app(win)  # type: ignore

        def _bootstrap(window):
            start_tray(window, window_api)
            uvicorn.run("server.api:app", host=HOST, port=API_PORT, reload=False)

        webview.start(_bootstrap, args=(win,))
