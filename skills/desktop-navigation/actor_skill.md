# Desktop Navigation — Actor Guide

Switches between running apps, launches apps, and navigates the taskbar.

## Switching to a Running App

Prefer taskbar click: read the app icon from `Taskbar Elements` in System Context and click it.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "AppName taskbar icon", "history": "Clicked AppName on taskbar"}
```

For pinned apps at position 1–9:

```json
{"action": "press_hotkey", "keys": ["win", "3"], "history": "Switched to pinned app position 3"}
```

Last resort for any running window:

```json
{"action": "press_hotkey", "keys": ["alt", "tab"], "history": "Cycling through open windows"}
```

## Launching an App

If no `launch-windows-app` skill is available, use Start Menu search:

```json
{"action": "press_hotkey", "keys": ["win"], "history": "Opened Start Menu"}
{"action": "type", "text": "Notepad", "history": "Searched for Notepad"}
{"action": "press_key", "key": "enter", "history": "Launched app"}
```

## Window Control

Minimize, maximize, or show desktop:

```json
{"action": "press_hotkey", "keys": ["win", "down"], "history": "Minimized active window"}
{"action": "press_hotkey", "keys": ["win", "up"], "history": "Maximized active window"}
{"action": "press_hotkey", "keys": ["win", "d"], "history": "Showed desktop"}
```

## After Switching or Launching

**Always verify the app is active** before interacting with its UI. The next turn's `# App Context` shows the new active window. If focus did not change, dismiss any modal dialogs (`Escape`) and retry the switch.

## File Explorer

Navigate folders via tree clicks (left pane) or the address bar (`Ctrl+L` to focus). Select files and use right-click for context operations.