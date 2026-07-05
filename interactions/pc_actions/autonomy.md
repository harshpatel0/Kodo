# PC Actions (Mouse/Keyboard) — Autonomy Mode

Universal fallback input — works on any app, including ones incompatible with UIA (canvas elements, focus-required JS listeners, unsupported control types). Tradeoff: steals focus and takes over mouse/keyboard, so the user cannot use their PC while it runs. Only use when `direct_app_control` cannot handle the interaction.

---

## SCHEMAS
```json
{"action": "click", "x": int, "y": int, "button": "left|right", "element": "string", "history": "string"}
{"action": "double_click", "x": int, "y": int, "button": "left|right", "element": "string", "history": "string"}
{"action": "type", "text": "string", "x": int, "y": int, "history": "string"}
{"action": "submit", "text": "string", "x": int, "y": int, "history": "string"}
{"action": "clear_field", "x": int, "y": int, "history": "string"}
{"action": "press_key", "key": "string", "history": "string"}
{"action": "press_hotkey", "keys": ["string"], "history": "string"}
{"action": "drag", "from_x": int, "from_y": int, "to_x": int, "to_y": int, "button": "left|right", "history": "string"}
```

---

## CONSTRAINTS
- **No blind focus:** Never emit `type` or `submit` without the target field confirmed as focused in the current tree.
- **Coordinate source of truth:** Use coordinates from the accessibility tree when the target element is present there. Use the screenshot only for elements the tree genuinely does not expose (canvas, custom widgets, web views). **When both are available, trust the accessibility tree** — it reflects the live, interactive state. The screenshot can be stale or misleading.

---

## ERROR RECOVERY
- Unexpected window focus change → `press_hotkey ["alt","tab"]` to recover, then re-verify.
- Element not in tree → `stuck` with a description of what was expected and what is present.
- Application hang or no UI change after two identical actions → `stuck` immediately.

---

## EXAMPLES
```json
{"action": "click", "x": 120, "y": 1050, "button": "left", "element": "Chrome", "history": "Clicked Chrome taskbar icon; browser now opening"}
{"action": "submit", "text": "Python tutorial", "x": 300, "y": 80, "history": "Submitted search query into focused search box"}
{"action": "press_hotkey", "keys": ["alt", "tab"], "history": "Active window changed unexpectedly; cycling back to target application"}
{"action": "press_hotkey", "keys": ["alt", "tab"], "history": "Click at (825,928) activated VSCode instead of target; recovering focus"}
```