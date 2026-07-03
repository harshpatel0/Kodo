import sys
import json
import os
import subprocess
import psutil
import time
import ctypes
import ctypes.wintypes
import threading


def get_all_windows_apps():
    """Queries the Windows Start Menu index directly to get ALL launchable apps
    (both classic Win32 apps and modern UWP/Store apps) in one pass.
    """
    app_map = {}
    normalized_seen = {}

    ps_command = (
        "Get-StartApps | ForEach-Object { "
        'if ($_.AppId) { echo "$($_.Name)||$($_.AppId)" } '
        "}"
    )

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            check=True,
            startupinfo=startupinfo,
        )

        for line in result.stdout.splitlines():
            if "||" in line:
                friendly_name, app_id = line.split("||", 1)
                name = friendly_name.strip()
                name_lower = name.lower()

                norm_name = "".join(c for c in name_lower if c.isalnum())

                if norm_name not in normalized_seen:
                    is_url = app_id.startswith("http")
                    if is_url:
                        continue
                    if ":" in app_id and not app_id.startswith("{"):
                        app_map[name_lower] = app_id
                    else:
                        app_map[name_lower] = f"shell:AppsFolder\\{app_id}"

                    normalized_seen[norm_name] = name_lower
                else:
                    existing_key = normalized_seen[norm_name]
                    if len(name_lower) < len(existing_key):
                        launch_path = app_map.pop(existing_key)
                        app_map[name_lower] = launch_path
                        normalized_seen[norm_name] = name_lower

    except Exception as e:
        print(f"Error indexing apps: {e}", file=sys.stderr)

    return app_map


def _launch_background(app_name, target, is_uwp):
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    shell32 = ctypes.windll.shell32

    SEE_MASK_NOCLOSEPROCESS = 0x00000040
    SEE_MASK_FLAG_NO_UI = 0x00000400
    SW_SHOWMINNOACTIVE = 7
    LSFW_LOCK = 1
    LSFW_UNLOCK = 2

    user32.LockSetForegroundWindow(LSFW_LOCK)

    class SHELLEXECUTEINFOW(ctypes.Structure):
        _fields_ = [
            ("cbSize", ctypes.wintypes.DWORD),
            ("fMask", ctypes.wintypes.ULONG),
            ("hwnd", ctypes.wintypes.HWND),
            ("lpVerb", ctypes.wintypes.LPCWSTR),
            ("lpFile", ctypes.wintypes.LPCWSTR),
            ("lpParameters", ctypes.wintypes.LPCWSTR),
            ("lpDirectory", ctypes.wintypes.LPCWSTR),
            ("nShow", ctypes.c_int),
            ("hInstApp", ctypes.wintypes.HINSTANCE),
            ("lpIDList", ctypes.c_void_p),
            ("lpClass", ctypes.wintypes.LPCWSTR),
            ("hkeyClass", ctypes.wintypes.HKEY),
            ("dwHotKey", ctypes.wintypes.DWORD),
            ("hIcon", ctypes.wintypes.HANDLE),
            ("hProcess", ctypes.wintypes.HANDLE),
        ]

    sei = SHELLEXECUTEINFOW()
    sei.cbSize = ctypes.sizeof(sei)
    sei.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_FLAG_NO_UI
    sei.lpVerb = "open"
    sei.lpFile = target
    sei.nShow = SW_SHOWMINNOACTIVE
    sei.hProcess = None

    ok = shell32.ShellExecuteExW(ctypes.byref(sei))
    if not ok:
        err = kernel32.GetLastError()
        user32.LockSetForegroundWindow(LSFW_UNLOCK)
        print(
            f"Failed to launch {app_name} in background (ShellExecuteExW error {err})",
            file=sys.stderr,
        )
        return None

    if sei.hProcess:
        kernel32.CloseHandle(sei.hProcess)

    time.sleep(4)

    user32.LockSetForegroundWindow(LSFW_UNLOCK)

    print(f"Launched {app_name} in background")
    return None


def open_app(app_name, background=False):
    if not app_name:
        print("Error: No app name.", file=sys.stderr)
        return

    app_map = get_all_windows_apps()
    target = next(
        (path for name, path in app_map.items() if name.lower() == app_name.lower()),
        None,
    )

    if not target:
        print(f"App {app_name} not found and could not be launched", file=sys.stderr)
        return

    is_uwp = "!" in target

    if background:
        return _launch_background(app_name, target, is_uwp)

    deadline = time.time() + 10

    os.startfile(target)
    exe_name = os.path.basename(target).lower()

    if is_uwp:
        time.sleep(3)
        print(f"Launched {app_name}")
        return

    while time.time() < deadline:
        if any(p.name().lower() == exe_name for p in psutil.process_iter(["name"])):
            print(f"Launched and verified: {app_name}")
            return
        time.sleep(0.5)
    print(f"Launched {app_name} but could not verify")


def get_list_of_installed_apps():
    return get_all_windows_apps().keys()


def generate_context():
    app_map = get_all_windows_apps()
    apps = list(app_map.keys())
    apps_str = ", ".join(apps)

    context = {
        "planner": f"""
## App Launcher — Strategic Guide
### Capability
You can bypass manual UI navigation by launching apps directly
Use this to move the task forward instantly.
### Available Apps on this PC:
{apps_str}

### Planning Rules
1. **Validation**: Only plan to open apps listed above. If an app isn't listed, search the web instead.
2. **State Transition**: A launch step is only 'Done' when the app is confirmed as the active window.
3. **Avoid the Trap**: Never plan a step to 'Click the Start Menu' if the app is in the list above.
4. **DirectAppControl**: When using DirectAppControl to control an app, pass `"background": true` to launch without stealing focus and return its PID for connection.
    """,
        "actor": f"""
## App Launcher — Tactical Guide

### ⚠️ AUTONOMY MODE
If the Planner requests an app name that is slightly different from the grid below
(e.g., 'Chrome' vs 'Google Chrome'), use your autonomy to select the correct match.
### Installed Apps:
[{apps_str}]
### Execution Action
```json
{{"action": "open_app", "app": "name"}}
```
Include `"background": true` when the app should launch without focus and you need its PID (e.g., for DirectAppControl).

### Recovery Protocol
- If `open_app` fails: Do NOT retry. Check if the app is already running in the Taskbar.
- If multiple versions exist: Default to the one that matches the Planner's intent.
- If `open_app` fails and the app is not running, navigate the start menu and search to open the relevant app and open it there.
  """,
    }
    print(json.dumps(context))
    sys.exit(0)


if __name__ == "__main__":
    if "--generate" in sys.argv:
        generate_context()

    args = json.loads(sys.argv[1])
    print(open_app(args.get("app"), background=args.get("background", False)))
