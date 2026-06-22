# Python Engine — Actor Guide

Execute Python code for system operations not covered by a loaded skill or standard UI interaction.

```json
{"action": "python", "code": "import subprocess; subprocess.Popen(['notepad.exe']); print('Launched')", "history": "string"}
```

## When to Use
- Download files from URLs
- Run shell, cmd, or PowerShell commands
- Interact with installed apps via CLI
- Calculations or string transformations no skill covers

## When NOT to Use
- A loaded skill covers the task — always prefer skill actions
- UI interactions inside a running app — use click/type instead
- Anything requiring visual confirmation of UI state

## Code Rules
- One logical operation per action
- Use stdlib only — packages will be auto-installed if detected, but prefer stdlib
- Always end with `print('confirmation message')` — no print means the action is treated as failed
- No blocking code (`input()`, infinite loops) — 15-second timeout enforced

## Examples

Download a file:
```json
{"action": "python", "code": "import urllib.request; urllib.request.urlretrieve('https://example.com/file.zip', 'C:\\\\Users\\\\User\\\\Downloads\\\\file.zip'); print('Downloaded')", "history": "Downloaded file to Downloads folder"}
```

Run PowerShell:
```json
{"action": "python", "code": "import subprocess; r = subprocess.run(['powershell', '-Command', 'Get-Process'], capture_output=True, text=True); print(r.stdout[:500])", "history": "Ran Get-Process via PowerShell"}
```

Print output becomes the next turn's context.