# Watchdogs

Watchdogs allow you to send a `read_only` action for Kodo to watch it for you, when it changes or the timeout expires, it will automatically return the result. Use this when you want to be alerted when something changes without calling the same action.

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
