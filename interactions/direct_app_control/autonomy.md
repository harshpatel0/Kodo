# Direct App Control (UIA) — Autonomy Mode

Controls running Windows apps in the background via UI Automation. No focus stealing, no mouse/keyboard takeover, no visible cursor movement — the user can keep working while this runs. Always try this before falling back to `pc_actions`.

You do not need to bring the app into focus to use Direct App Control. As long as you're confident the app is launched, hook into it directly — that's the whole point: never steal focus from the user.

The accessibility tree from `pc_actions` only shows the currently focused window. Direct App Control bypasses this — it can discover, connect to, and control any running app regardless of focus. Use `list_processes` to discover apps; don't rely on tree/focus state.

**Testing status:** In active testing — prefer it. If a task is not feasible with Direct App Control because it requires focus, do not attempt a workaround: surface a toast notification explaining what happened in detail and call `done` prematurely.

---

## RULE: NEVER LAUNCH OR NAVIGATE IF THE APP IS ALREADY OPEN

If the task or user tells you an app is already running (e.g. "Edge is already open", "the form is open in the browser"), **do not launch it**. Do not navigate to a URL, do not use `open_app`, do not use pc_actions to find a window. Start directly with:

1. **`list_processes`** — find the running process
2. **`connect(process_id)`** — attach to it
3. Proceed with `list_controls` and interact

**Do not verify** the connection via screenshots, pc_actions, or the accessibility tree. The DAC control tree is authoritative — if you're connected, you have the controls. Proceed immediately.

---

## SCHEMAS
```json
{"action": "list_processes", "history": "string"}
{"action": "connect", "process_id": int, "history": "string"}
{"action": "list_controls", "history": "string"}
{"action": "interact", "control_id": "string", "value": "string (optional, for value-supporting controls like Edit, or ComboBox fallback)", "history": "string"}
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
1. **`list_processes`** — discover running top-level windows → pick the right `process_id`. This is always step one. Never skip it.
2. **`connect`** — attach to that `process_id`. When `direct_app_control.always_populate_connected_app_controls` is `true` (default), `connect` auto-runs `list_controls` and returns the control tree in its response — you can skip the separate call. Must be done before any other control action.
3. **Evaluate & Act:** Pick the matching action based on the control `type` and act using its `control_id`. Trust the control list — do not cross-reference with screenshots or pc_actions.
4. **Dynamic UI Updates:** If interacting with a container reveals new items (e.g. `expand` on a ComboBox), you **MUST run `list_controls` again** to get runtime IDs of newly revealed child elements before selecting them.

You can re-`connect` to switch apps. No explicit disconnect needed.

---

## NOTES & CONSTRAINTS
- **Connection first:** Must connect before `list_controls` or any action — calls fail with "Not connected" otherwise.
- **Unstable IDs:** `control_id` is a session-scoped runtime ID. Not stable across app restarts or re-connects. Always get fresh IDs from `list_controls` after connecting.
- **DAC exposes CSS-hidden controls:** The UIA tree includes elements hidden by CSS (`display: none`). If a control appears in `list_controls` but `interact` returns "Control not found", it may be gated by a conditional field (e.g. a dropdown that only appears after selecting an option). Find the trigger control first, interact with it, then re-list controls.
- **ComboBoxes/Dropdowns — priority order:**
  1. `expand` the ComboBox, run `list_controls` to find the newly visible ListItem, then `interact` with that ListItem. The handler fires both `Select` and `Invoke` — this ensures JavaScript `change` events fire on HTML `<select>` elements.
  2. If `expand` returns a COM error (`Expand failed: (-2146233079, ...)`), the control may be stale or lack ExpandCollapse. Fall back to `set_value` on the ComboBox directly with the desired value.
  3. If both fail, use `pc_actions` to click the dropdown and its option.
- **Minimized windows included in list_processes:** `list_processes` now shows windows even when minimized or in the background, as long as they have a title. You can `connect` to any listed PID regardless of window state.
- **Filtered controls:** Structural containers (Pane, Group, Window-as-wrapper, Custom) are filtered out of `list_controls` — don't try to interact with them.
- **Debugging:** Every action returns `{success, method, message}`. `method` tells you which UIA pattern fired (e.g. "toggle", "value_pattern", "legacy"). "No supported pattern" means the control needs a different function (e.g. a Slider needs `set_range_value`, a ComboBox needs `expand`).
- **Focus limits:** DAC does NOT steal focus. All UIA patterns used (Select, SetValue, Toggle, Expand, Scroll, RangeValue) are focus-neutral per spec. `Invoke` is also spec'd as focus-neutral, but some browser providers may still steal focus — if you observe this, use `Select` on ListItems instead (it triggers JS `change` events without Invoke on most sites), or use `set_value` directly on the parent ComboBox. If a task genuinely requires focus-based input, fall back to `pc_actions`.

---

## EXAMPLES
```json
{"action": "list_processes", "history": "Listing available windows"}
{"action": "connect", "process_id": 1234, "history": "Connected to notepad.exe"}
{"action": "list_controls", "history": "Listing all controls in the connected window"}
{"action": "interact", "control_id": "12-345678-9", "history": "Clicked Edit button"}
{"action": "set_value", "control_id": "12-345678-9", "value": "hello world", "history": "Typed into edit field"}
{"action": "scroll", "control_id": "12-345678-9", "direction": "down", "amount": "line", "history": "Scrolled down one line"}
{"action": "expand", "control_id": "12-345678-10", "history": "Expanded ComboBox to reveal dropdown options"}
```