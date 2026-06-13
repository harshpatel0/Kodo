# Desktop Navigation — Actor Guide

---

## CORE RULE: CHECK THE ACTIVE WINDOW FIRST

Before taking any action, you must know what window is currently in focus.
The "Active Window" is provided in the `# App Context` section of each turn.

**Never assume an app is open.** Always verify by reading the active window title.

---

## DECISION TREE

```
Is the app already active?
├── YES → Proceed with the task directly. Do not launch anything.
└── NO  → Is the app already running but not focused?
          ├── YES → Switch to it (see Switching To A Running App)
          └── NO  → Launch the app (see Launching An App)
```

---

## SWITCHING TO A RUNNING APP

### Method 1 — Click the taskbar icon (preferred)

Read the `Taskbar Elements` section in the `# System Context` of your prompt.
It lists every icon visible on the taskbar with its control type, name, and coordinates.

Find the icon for your target app (e.g., "Chrome", "Notepad", "File Explorer")
and click it:

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "AppName taskbar icon", "history": "Clicked AppName icon on taskbar to switch focus"}
```

**Do not guess coordinates.** Always read the exact `x` and `y` from the
Taskbar Elements list. If the taskbar is not visible, it may be hidden —
press `Win+T` to focus the taskbar first, then re-read the tree.

### Method 2 — Win + Number key (pinned apps only, positions 1–9)

If the app is **pinned** to the taskbar and you know its position
(left-to-right, starting at 1), you can use the keyboard shortcut:

```json
{"action": "press_hotkey", "keys": ["win", "3"], "history": "Switched to pinned app at position 3 on the taskbar"}
```

**Rules:**
- Only works for **pinned** taskbar items. If unsure whether it is pinned, use Method 1.
- Only positions **1 through 9** are accessible this way.
- Position 1 is the leftmost icon (excluding the Start button / Windows icon).
- This shortcut switches to the app if already running, or launches it if not.

### Method 3 — Alt + Tab (last-resort for any running window)

If you cannot find the app icon on the taskbar but the app is already running
(e.g., minimized to system tray or hidden under other windows):

```json
{"action": "press_hotkey", "keys": ["alt", "tab"], "history": "Cycling through open windows via Alt+Tab"}
```

**Warning:** `Alt+Tab` may require multiple presses or a long press to find
the target window. Prefer Method 1 or 2 when possible.

---

## LAUNCHING AN APP

If the app is **not** running and no `launch-windows-app` skill is available,
use the Start Menu search:

1. Press `Win` key to open Start Menu
2. Type the app name
3. Press `Enter` to launch

```json
{"action": "press_hotkey", "keys": ["win"], "history": "Opened Start Menu"}
{"action": "type", "text": "Notepad", "history": "Typed app name into Start Menu search"}
{"action": "press_key", "key": "enter", "history": "Pressed Enter to launch app"}
```

If a `launch-windows-app` skill **is** available, prefer it:

```json
{"action": "open_app", "app": "Notepad", "history": "Using skill to launch Notepad"}
```

---

## AFTER LAUNCHING — VERIFYING FOCUS

After any launch or switch action, always confirm the app is the active window
before interacting with its UI elements.

**The next turn's `# App Context` will show you the new active window.**
If the target app is still not the active window:
- It may still be loading — wait and re-check
- It may have opened but not gained focus — use the taskbar click
- It may have failed to launch — retry

---

## PERSISTENT APP DETECTION

If an app appears in the taskbar but clicking it does not bring it to focus:
1. The app may have a pop-up or dialog open (e.g., "Save As", "Unsaved changes")
2. First dismiss any modal dialogs by pressing `Escape`
3. Then try the taskbar click again

```json
{"action": "press_key", "key": "escape", "history": "Dismissed potential modal dialog before switching"}
```

---

## WINDOW MANAGEMENT

### Minimize, Maximize, Restore, Close

Use the window's title bar buttons if visible in the accessibility tree:

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "Minimize / Maximize / Close button", "history": "Clicked window control button"}
```

Keyboard alternatives:
- **Alt+F4** — Close the active window
- **Win+Up** — Maximize the active window
- **Win+Down** — Restore / Minimize the active window
- **Win+M** — Minimize all windows
- **Win+D** — Show desktop (toggle)

```json
{"action": "press_hotkey", "keys": ["alt", "f4"], "history": "Closed active window"}
```

### Move a Window

Drag the title bar to reposition:

```json
{"action": "drag", "from_x": int, "from_y": int, "to_x": int, "to_y": int, "button": "left", "duration": 0.3, "history": "Moved window to new position"}
```

Get the title bar coordinates from the accessibility tree — look for a
`TitleBar` control or the top edge of the `Window`/`Pane` element.

### Snap a Window to a Screen Half / Corner

```json
{"action": "press_hotkey", "keys": ["win", "left"], "history": "Snapped window to left half of screen"}
{"action": "press_hotkey", "keys": ["win", "right"], "history": "Snapped window to right half of screen"}
{"action": "press_hotkey", "keys": ["win", "up"], "history": "Snapped window to top half or maximized"}
```

### Resize a Window

Find the window border or corner in the accessibility tree and drag it:

```json
{"action": "drag", "from_x": int, "from_y": int, "to_x": int, "to_y": int, "button": "left", "duration": 0.3, "history": "Resized window by dragging border"}
```

---

## FILE EXPLORER NAVIGATION

### Common Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` or `Alt+D` | Focus the address bar |
| `F4` | Focus the address bar with dropdown |
| `Ctrl+F` or `F3` | Focus the search box |
| `F5` | Refresh the view |
| `Ctrl+Shift+N` | Create a new folder |
| `F2` | Rename selected item |
| `F11` | Toggle full-screen |
| `Alt+Left` | Back to previous folder |
| `Alt+Right` | Forward to next folder |
| `Alt+Up` | Go up one folder level |
| `Ctrl+C`, `Ctrl+X`, `Ctrl+V` | Copy, Cut, Paste |

### Navigating the Folder Tree

The left pane (navigation pane) contains a tree view of drives and folders.
Use clicks to expand/collapse tree items and navigate the hierarchy.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "Desktop tree item", "history": "Navigated to Desktop in folder tree"}
```

### File Operations

Click a file or folder to select it. Use `Ctrl+Click` for multi-select or
`Shift+Click` for range-select.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "report.docx", "history": "Selected report.docx"}
```

### Right-Click Context Menu

For file operations (rename, delete, properties, open with, etc.):

```json
{"action": "click", "x": int, "y": int, "button": "right", "element": "report.docx", "history": "Opened context menu on report.docx"}
```

After right-clicking, wait for the context menu to appear in the accessibility
tree, then click the desired option.

Keyboard alternative: select the file first, then use `Shift+F10` or the
context-menu key.

---

## START MENU & SEARCH

### Open Start Menu

```json
{"action": "press_key", "key": "win", "history": "Opened Start Menu"}
```

### Search from Start

After pressing `Win`, Start opens with the search box already focused.
Just type your query.

```json
{"action": "press_key", "key": "win", "history": "Opened Start Menu with search focused"}
{"action": "type", "text": "Calculator", "history": "Searched for Calculator"}
{"action": "press_key", "key": "enter", "history": "Launched Calculator from search results"}
```

### Run Dialog (Win+R)

```json
{"action": "press_hotkey", "keys": ["win", "r"], "history": "Opened Run dialog"}
{"action": "type", "text": "notepad", "history": "Typed notepad in Run dialog"}
{"action": "press_key", "key": "enter", "history": "Pressed Enter in Run dialog"}
```

---

## SYSTEM TRAY / NOTIFICATION AREA

The system tray (bottom-right of the screen) contains icons for background
apps, volume, network, clock, etc.

**Accessing system tray icons:**
- The system tray has a "Show hidden icons" (chevron) button. Click it to
  expand if your target icon is not visible in the tree.
- Icons may be under the chevron overflow panel.
- The clock, volume, network, and action center icons are always visible.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "Show hidden icons chevron", "history": "Expanded system tray overflow"}
```

### Action Center (Win+A)

```json
{"action": "press_hotkey", "keys": ["win", "a"], "history": "Opened Action Center"}
```

Contains quick settings toggles (Wi-Fi, Bluetooth, Focus Assist, etc.) and
notifications. Click a toggle to change its state.

---

## CONTEXT MENUS

Right-clicking opens a context menu. Wait for the menu to appear in the
accessibility tree before picking an item.

**Always right-click first, then click the option:**

```json
{"action": "click", "x": int, "y": int, "button": "right", "element": "Target element", "history": "Right-clicked target element"}
```

On the next turn, the accessibility tree will show the context menu items.
Click the desired option:

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "Copy / Delete / Properties option", "history": "Clicked Copy in context menu"}
```

**Keyboard alternative:** `Shift+F10` or the context-menu key (between
Right-Alt and Right-Ctrl on most keyboards) opens the context menu for the
currently focused/selected element.

---

## COMMON DIALOG BOX PATTERNS

### Open / Save File Dialog

The dialog has:
- **Address bar / breadcrumb nav** at the top
- **File name** text input at the bottom
- **File type** dropdown at the bottom
- **Open / Save** button
- **Cancel** button
- **Navigation pane** on the left (Quick Access, This PC, etc.)

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "File name edit", "history": "Focused file name input in save dialog"}
{"action": "type", "text": "document.txt", "x": int, "y": int, "history": "Typed file name"}
{"action": "click", "x": int, "y": int, "button": "left", "element": "Save button", "history": "Clicked Save"}
```

To navigate to a different folder in the save dialog, use `Ctrl+L` to focus
the address bar, type the path, and press Enter.

### Confirmation Dialogs (Yes / No / Cancel)

Windows shows dialogs with buttons like "Yes", "No", "Cancel", "Don't Save",
"OK", "Apply". Read them from the tree and click the appropriate one.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "Don't Save button", "history": "Clicked Don't Save on unsaved changes dialog"}
```

**Keyboard shortcut:** `Enter` confirms the default button. `Tab` navigates
between buttons. `Escape` cancels / closes the dialog.

### Error / Warning Dialogs

Error dialogs have an "OK" button and sometimes "Details" or "More info"
links. Click OK to dismiss.

```json
{"action": "press_key", "key": "enter", "history": "Dismissed error dialog with Enter"}
```

---

## COMMON UI CONTROLS

### Dropdown / ComboBox

A ComboBox typically shows a text value with a chevron button. Click the
chevron or the combo box itself to expand the list, then click an item.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "File type ComboBox", "history": "Expanded file type dropdown"}
```

The accessibility tree will then show the expanded list items. Click the
desired value.

### CheckBox

A CheckBox has two or three states: checked, unchecked, and sometimes
indeterminate. Click to toggle.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "CheckBox name", "history": "Toggled checkbox"}
```

### RadioButton

Radio buttons are grouped. Clicking one selects it and deselects the others
in the same group.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "RadioButton name", "history": "Selected radio option"}
```

### List / ListItem

Lists show a set of selectable items. Click an item to select it.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "ListItem name", "history": "Selected item from list"}
```

### Tree / TreeItem

Tree views show hierarchical data with expand/collapse chevrons. Click a
chevron or double-click an item to expand it.

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "TreeItem name", "history": "Expanded tree node"}
```

### Slider

Sliders are adjusted by dragging the thumb. Alternatively, click the track
on either side of the thumb to increment/decrement.

```json
{"action": "drag", "from_x": int, "from_y": int, "to_x": int, "to_y": int, "button": "left", "duration": 0.3, "history": "Dragged slider to new value"}
```

### Tab / TabItem

Tabs switch between pages of content. Click a tab to activate it:

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "TabItem name", "history": "Switched to tab"}
```

### ProgressBar

A ProgressBar is display-only. Do not try to interact with it.
Read its value from the tree to determine progress.

### Hyperlink

Click a hyperlink to navigate:

```json
{"action": "click", "x": int, "y": int, "button": "left", "element": "Hyperlink text", "history": "Clicked hyperlink"}
```

### ToolBar

Toolbars contain action buttons (e.g., "Cut", "Copy", "Paste", "Bold").
Find the button in the tree and click it.

---

## KEYBOARD NAVIGATION

When mouse interaction is unreliable, use keyboard navigation.

### Tab Stops

| Key | Action |
|-----|--------|
| `Tab` | Move focus to the next control |
| `Shift+Tab` | Move focus to the previous control |
| `Space` | Activate the focused button or toggle a checkbox |
| `Enter` | Activate the focused button or confirm a dialog |
| `Escape` | Cancel / close dialog or menu |
| `Arrow keys` | Navigate within a group (radio buttons, list items, tabs) |

### Text Editing

| Shortcut | Action |
|----------|--------|
| `Ctrl+A` | Select all text |
| `Ctrl+C` | Copy selection |
| `Ctrl+X` | Cut selection |
| `Ctrl+V` | Paste clipboard |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` or `Ctrl+Shift+Z` | Redo |
| `Ctrl+Left` / `Ctrl+Right` | Jump word-by-word |
| `Ctrl+Shift+Left` / `Ctrl+Shift+Right` | Select word-by-word |
| `Home` / `End` | Start / End of line |
| `Ctrl+Home` / `Ctrl+End` | Start / End of document |

### Common Dialog Navigation

- **Ctrl+Tab** / **Ctrl+Shift+Tab** — Cycle forward/backward through tabs
- **Ctrl+PageUp** / **Ctrl+PageDown** — Previous/next tab
- **Alt+UnderlinedLetter** — Activate a menu or button by its accelerator key
- **Alt+Space** — Open the window control menu (restore, move, size, minimize, maximize, close)

---

## SCROLLING

### Scroll Vertically

```json
{"action": "scroll_v", "amount": -3, "x": int, "y": int, "history": "Scrolled down 3 units in content pane"}
```

Positive amount scrolls up, negative scrolls down.

### Scroll Horizontally

```json
{"action": "scroll_h", "amount": 3, "x": int, "y": int, "history": "Scrolled right in content pane"}
```

### Page Up / Page Down

```json
{"action": "press_key", "key": "pagedown", "history": "Scrolled down one page"}
```

### Scroll to a Specific Element

If you know the target element exists in the tree but it is off-screen,
scroll in the direction that would bring it into view, then re-check the tree.

---

## TASK VIEW & VIRTUAL DESKTOPS

### Open Task View

```json
{"action": "press_hotkey", "keys": ["win", "tab"], "history": "Opened Task View"}
```

Task View shows all open windows for the current virtual desktop, plus
any additional virtual desktops along the bottom. Click a window thumbnail
to switch to it.

### Create a New Virtual Desktop

```json
{"action": "press_hotkey", "keys": ["win", "ctrl", "d"], "history": "Created new virtual desktop"}
```

### Switch Virtual Desktops

```json
{"action": "press_hotkey", "keys": ["win", "ctrl", "left"], "history": "Switched to previous virtual desktop"}
{"action": "press_hotkey", "keys": ["win", "ctrl", "right"], "history": "Switched to next virtual desktop"}
```

### Close Current Virtual Desktop

```json
{"action": "press_hotkey", "keys": ["win", "ctrl", "f4"], "history": "Closed current virtual desktop"}
```

---

## MULTI-MONITOR NAVIGATION

### Move Active Window to Another Monitor

```json
{"action": "press_hotkey", "keys": ["win", "shift", "left"], "history": "Moved window to left monitor"}
{"action": "press_hotkey", "keys": ["win", "shift", "right"], "history": "Moved window to right monitor"}
```

### Screen Coordinates Context

The `# App Context` tells you the screen resolution (e.g., `1920x1080`).
If the taskbar y-value is close to 1080, you are on the primary monitor.
Coordinates for secondary monitors may extend beyond these bounds
(e.g., x values from 1920 to 3839 on a dual-monitor setup).

---

## TASK MANAGER

### Open Task Manager

```json
{"action": "press_hotkey", "keys": ["ctrl", "shift", "escape"], "history": "Opened Task Manager"}
```

In Task Manager:
- The "Processes" tab shows running apps and background processes
- Right-click a process for actions: "End task", "Open file location", etc.
- Use Tab to navigate between sections
- If Task Manager opens in compact view, click "More details" to expand

---

## COMMON FAILURE PATTERNS

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Click lands but nothing changes | App not the active window | Switch to the app first, then re-click |
| Typed text goes to wrong window | Focus is still on previous app | Switch focus explicitly before typing |
| Keyboard shortcut does nothing | Taskbar may be auto-hidden | Move mouse to screen bottom, then try again |
| Win+Number launches the wrong app | Position count was off | Re-count pinned items from the left (position 1) |
| Dialog appears but buttons not visible | Dialog loading or animated | Wait a turn and re-read the tree |
| Right-click menu is empty | Menu loading or click missed | Retry the right-click, ensure coordinates are exact |
| Text input does not accept typing | Field not focused or disabled | Click the field first to focus, then type |
| Scroll does not move the content | Wrong coordinates — scrolled in empty area | Target the scrollable pane, not the window background |

---

## SUMMARY

1. **Always check the active window** before acting
2. **Taskbar click** is the preferred switch method
3. **Win+1 through Win+9** for pinned apps at known positions
4. **Alt+Tab** only as a fallback
5. After launching, verify focus changed before the next action
6. **Right-click first, then click the menu item** for context menus
7. Use **keyboard shortcuts** when mouse interaction is unreliable
8. **Read the accessibility tree** every turn — it is your source of truth
9. **Scroll to reveal** off-screen elements before attempting to click them
10. **Dismiss dialogs** with Escape or Enter before proceeding
