import sys
import json
import os
import glob
import subprocess


def get_all_windows_apps():
    app_map = {}

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
                clean_name = friendly_name.strip().lower()

                # If it's already a standard path or GUID, handle it,
                # otherwise prefix it so os.startfile knows how to open it
                if ":" in app_id or app_id.startswith("{"):
                    app_map[clean_name] = app_id
                else:
                    app_map[clean_name] = f"shell:AppsFolder\\{app_id}"
    except Exception:
        pass

    return app_map


def open_app(app_name):
    if not app_name:
        print("Error: No app name.", file=sys.stderr)
    app_map = get_all_windows_apps()
    target = next(
        (path for name, path in app_map.items() if name.lower() == app_name.lower()),
        None,
    )

    if target:
        os.startfile(target)
        print(f"Launched {app_name}")
    else:
        print(f"App {app_name} not found.", file=sys.stderr)


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
    print(open_app(args.get("app")))
