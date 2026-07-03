# Direct App Control (UIA) — Autonomy Mode

Controls running Windows apps in the background via UI Automation. No focus stealing, no mouse/keyboard takeover, no visible cursor movement — the user can keep working while this runs. Always try this before falling back to `pc_actions`.

You do not need to bring the app into focus to use Direct App Control. As long as you're confident the app is launched, hook into it directly — that's the whole point: never steal focus from the user.

The accessibility tree from `pc_actions` only shows the currently focused window. Direct App Control bypasses this — it can discover, connect to, and control any running app regardless of focus. Use `list_processes` to discover apps; don't rely on tree/focus state.

**Testing status:** In active testing — prefer it. If a task is not feasible with Direct App Control because it requires focus, do not attempt a workaround: surface a toast notification explaining what happened in detail and call `done` prematurely.

---

## SCHEMAS
```json
{"action": "list_processes", "history": "string"}
{"action": "connect", "process_id": int, "history": "string"}
{"action": "list_controls", "control_id": "string", "history": "string"}
{"action": "interact", "control_id": "string", "value": "string (optional, for setting ComboBox values directly)", "history": "string"}
{"action": "expand", "control_id": "string", "history": "string"}
{"action": "collapse", "control_id": "string", "history": "string"}
{"action": "set_value", "control_id": "string", "value": "string", "history": "string"}
{"action": "scroll", "control_id": "string", "direction": "up|down|left|right", "amount": "line|page", "history": "string"}
{"action": "set_range_value", "control_id": "string", "value": float, "history": "string"}
{"action": "get_grid_item", "control_id": "string", "row": int, "col": int, "history": "string"}
{"action": "minimize_window", "control_id": "string", "history": "string"}
{"action": "maximize_window", "control_id": "string", "history": "string"}
{"action": "restore_window", "control_id": "string", "history": "string"}
{"action": "close_window", "control_id": "string", "history": "string"}
```

---

## MANDATORY INTERACTION SEQUENCE
1. **`list_processes`** — discover running top-level windows → pick the right `process_id`.
2. **`connect`** — attach to that `process_id`. When `direct_app_control.always_populate_connected_app_controls` is `true` (default), `connect` auto-runs `list_controls` and returns the control tree in its response — you can skip the separate call. Must be done before any other control action.
3. **Evaluate & Act:** Pick the matching action based on the control `type` and act using its `control_id`.
4. **Dynamic UI Updates:** If interacting with a container reveals new items (e.g. `expand` on a ComboBox), you **MUST run `list_controls` again** to get runtime IDs of newly revealed child elements before selecting them.

You can re-`connect` to switch apps. No explicit disconnect needed.

---

## NOTES & CONSTRAINTS
- **Connection first:** Must connect before `list_controls` or any action — calls fail with "Not connected" otherwise.
- **Unstable IDs:** `control_id` is a session-scoped runtime ID. Not stable across app restarts or re-connects. Always get fresh IDs from `list_controls` after connecting.
- **ComboBoxes/Dropdowns:** Do not use `set_value` or standard `interact` to pick an item. `expand` the ComboBox, run `list_controls` to find the newly visible ListItem, then `interact` with that ListItem.
- **Filtered controls:** Structural containers (Pane, Group, Window-as-wrapper, Custom) are filtered out of `list_controls` — don't try to interact with them.
- **Debugging:** Every action returns `{success, method, message}`. `method` tells you which UIA pattern fired (e.g. "toggle", "value_pattern", "legacy"). "No supported pattern" means the control needs a different function (e.g. a Slider needs `set_range_value`, a ComboBox needs `expand`).
- **Focus limits:** Does not steal focus. If a task requires focus-based input (e.g. typing that must trigger onKeyPress-style JS listeners not covered by ValuePattern), this is the wrong layer — fall back to `pc_actions`.

---

## EXAMPLES
```json
{"action": "list_processes", "history": "Listing available windows"}
{"action": "connect", "process_id": 1234, "history": "Connected to notepad.exe"}
{"action": "list_controls", "control_id": "", "history": "Listing all controls in the connected window"}
{"action": "interact", "control_id": "12-345678-9", "history": "Clicked Edit button"}
{"action": "set_value", "control_id": "12-345678-9", "value": "hello world", "history": "Typed into edit field"}
{"action": "scroll", "control_id": "12-345678-9", "direction": "down", "amount": "line", "history": "Scrolled down one line"}
{"action": "expand", "control_id": "12-345678-10", "history": "Expanded ComboBox to reveal dropdown options"}
```