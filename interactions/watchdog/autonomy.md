# Watchdogs

Send a read-only action once; Kodo re-runs it in the background and returns the result the moment it changes, or at timeout — no manual re-polling.

---

## SCHEMA

```json
{"action": "watchdog", "watchdog_action": {"action": "...", "..."}, "timeout": "...", "history": "string"}
```

The default `timeout` is `15`.

---

## CONSTRAINTS

Only watch read-only actions — never one that changes state. `pc_actions` and `direct_app_control` are disallowed except `list_processes`/`list_controls` (read-only). Skills that already implement their own wait-for-completion protocol (e.g. `launch_windows_app`) should not be wrapped in a watchdog — trust the skill's own protocol instead.

A returned result — changed or timed out — IS the confirmation; see Core Principles on trusting convenience mechanisms.

`clipboard_read` — okay to watch (read-only). `open_app` from `launch_windows_app` — not okay (changes PC state, has its own protocol).
