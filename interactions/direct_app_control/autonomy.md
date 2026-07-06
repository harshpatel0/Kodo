## DIRECT APP CONTROL (DAC)

UIA-based control of running apps — no focus steal, no cursor movement. Try before `pc_actions`. App need not be focused or foregrounded to control.

**If already open:** never `open_app`/navigate. Go straight to `list_processes` → `connect` → act. Skip verification via screenshot/tree — DAC's control list is authoritative.

**If connect fails** (claimed-open app not found): `retry` once with fresh `list_processes`, then `stuck` if still absent — don't guess-launch.

### SEQUENCE
1. `list_processes` → pick `process_id`. Always first, never skipped.
2. `connect` → attaches; auto-runs `list_controls` if `always_populate_connected_app_controls` (default true) — use that response, don't re-call.
3. Act on `control_id` matching control `type`.
4. Container reveals new children (e.g. `expand`) → re-`list_controls` for fresh IDs before touching them.

Re-`connect` to switch apps freely, no disconnect needed.

### SCHEMAS
```json
{"action": "list_processes", "history": "string"}
{"action": "connect", "process_id": int, "history": "string"}
{"action": "list_controls", "history": "string"}
{"action": "interact", "control_id": "string", "value": "string?", "history": "string"}
{"action": "expand", "control_id": "string", "history": "string"}
{"action": "collapse", "control_id": "string", "history": "string"}
{"action": "set_value", "control_id": "string", "value": "string", "history": "string"}
{"action": "scroll", "control_id": "string", "direction": "up|down|left|right", "amount": "line|page", "history": "string"}
{"action": "set_range_value", "control_id": "string", "value": float, "history": "string"}
{"action": "get_grid_item", "control_id": "string", "row": int, "col": int, "history": "string"}
{"action": "minimize_window|maximize_window|restore_window|close_window", "control_id": "string", "history": "string"}
```

### NOTES
- **IDs are session-scoped**, not stable across restart/reconnect — always fresh from `list_controls`.
- **Hidden-but-listed control** ("Control not found" on interact): likely gated by a trigger (e.g. conditional field). Find trigger, interact, re-list.
- **ComboBox, in order:** (1) `set_value` on the ComboBox itself with target text — works collapsed, no focus needed. (2) If fails: `expand` → `list_controls` → `interact` on the revealed ListItem. (3) If both fail: `pc_actions` click.
- **ComboBox items are visible pre-expand** in `list_controls` — no need to `expand` just to see options.
- **Minimized/background windows appear in `list_processes`** if titled — connect regardless of window state.
- **Structural containers (Pane/Group/wrapper Window/Custom) are pre-filtered** from `list_controls` — don't target them.
- **Focus:** all patterns here are focus-neutral by spec; some browser `Invoke` providers may steal focus anyway — if seen, prefer `Select` on the ListItem, or `set_value` on the parent ComboBox. Genuine focus-required input → fall back to `pc_actions`.
- **Infeasible-without-focus task:** don't force it through `pc_actions` as workaround here — toast the detail, `done` early.
- Every response returns `{success, method, message}` — `method` reveals which UIA pattern fired; "no supported pattern" means wrong action for that control type (e.g. Slider wants `set_range_value`).

### EXAMPLES
```json
{"action": "list_processes", "history": "Listing windows"}
{"action": "connect", "process_id": 1234, "history": "Connected to notepad.exe"}
{"action": "set_value", "control_id": "12-345678-9", "value": "hello world", "history": "Typed into edit field"}
{"action": "expand", "control_id": "12-345678-10", "history": "Expanded ComboBox"}
```