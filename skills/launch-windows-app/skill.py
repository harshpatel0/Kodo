import sys
import json
import os
import subprocess
import psutil
import time
import ctypes
import ctypes.wintypes


def get_all_windows_apps():
    """Queries the Windows Start Menu index to map friendly names to launch targets."""
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


def _launch_background(app_name, target):
    """Launches an app without stealing focus and attempts to retrieve its PID."""
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

    # Always unlock foreground window regardless of success
    user32.LockSetForegroundWindow(LSFW_UNLOCK)

    if not ok:
        err = kernel32.GetLastError()
        print(
            f"Failed to launch {app_name} in background (Error {err})", file=sys.stderr
        )
        return

    pid = None
    if sei.hProcess:
        pid = kernel32.GetProcessId(sei.hProcess)
        kernel32.CloseHandle(sei.hProcess)

    if pid:
        print(f"Launched {app_name} in background. PID: {pid}")
    else:
        print(
            f"Launched {app_name} in background. PID: Unknown (likely UWP app routed via DCOM)"
        )


def _launch_foreground(app_name, target, is_uwp):
    """Launches an app normally and attempts to verify via process scanning."""
    start_time = time.time()
    os.startfile(target)

    if is_uwp:
        time.sleep(2)
        print(
            f"Launched {app_name}. PID: Unknown (UWP apps abstract standard process IDs)"
        )
        return

    exe_name = os.path.basename(target).lower()
    deadline = start_time + 10

    while time.time() < deadline:
        for p in psutil.process_iter(["name", "create_time"]):
            try:
                if p.info["name"] and p.info["name"].lower() == exe_name:
                    if p.info["create_time"] >= (start_time - 1):
                        print(f"Launched and verified {app_name}. PID: {p.pid}")
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        time.sleep(0.5)

    print(f"Launched {app_name}.")


def open_app(app_name, background=False):
    if not app_name:
        print("Error: No app name provided.", file=sys.stderr)
        return

    app_map = get_all_windows_apps()
    target = next(
        (path for name, path in app_map.items() if name.lower() == app_name.lower()),
        None,
    )

    if not target:
        print(f"App '{app_name}' not found in system index.", file=sys.stderr)
        return

    is_uwp = "!" in target

    if background:
        _launch_background(app_name, target)
    else:
        _launch_foreground(app_name, target, is_uwp)


def generate_context():
    """Generates the dynamic LLM context based on the current system state."""
    app_map = get_all_windows_apps()
    apps = list(app_map.keys())
    apps_str = ", ".join(apps)

    context = {
        "planner": f"""## App Launcher - Planner Guide
### Capability
You can bypass manual UI navigation by launching apps directly.
Use this to move the task forward instantly.

### Available Apps on this PC:
{apps_str}

### Planning Rules
1. **Validation**: Only plan to open apps listed above. If an app isn't listed, search the web instead.
2. **State Transition**: A launch step is only 'Done' when the app is confirmed as launched.
3. **Avoid the Trap**: Never plan a step to 'Click the Start Menu' if the app is in the list above.
4. **DirectAppControl**: When using DirectAppControl, pass `"background": true` to launch without stealing focus. The action will return the process PID.
""",
        "actor": f"""## App Launcher - Actor Guide

### AUTONOMY MODE
If the Planner requests an app name that is slightly different from the grid below
(e.g., 'Chrome' vs 'Google Chrome'), use your autonomy to select the correct match.

### Installed Apps:
[{apps_str}]

### Execution Action
{{"action": "open_app", "app": "<app_name_as_provided>", "background": false}}

Set "background": true if the app should launch silently (e.g., when you need its PID for UI interaction without disrupting the user).

### Recovery Protocol
If open_app fails: Do NOT retry. Check if the app is already running in the Taskbar.
If multiple versions exist: Default to the one that matches the Planner's intent.
""",
    }

    print(json.dumps(context))
    sys.exit(0)


if __name__ == "__main__":
    if "--generate" in sys.argv:
        generate_context()

    try:
        args = json.loads(sys.argv[1])
    except (IndexError, json.JSONDecodeError):
        print(
            "Error: Invalid or missing JSON arguments provided to skill.",
            file=sys.stderr,
        )
        sys.exit(1)

    app = args.get("app")
    background = args.get("background", False)

    open_app(app, background)
