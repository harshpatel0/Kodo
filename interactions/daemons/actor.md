# Daemon Layer

Daemons run a tool call **every turn on your behalf** and inject the result into your context. You get fresh data without spending an action.

---

## SCHEMAS

```json
{"action": "create_daemon", "daemon_action": {...}, "history": "string"}
{"action": "unregister_daemon", "index": int, "history": "string"}
```

---

## When to daemonise

Any action you would otherwise call manually every turn to keep state fresh:
- `take_snapshot` on a page you're monitoring
- `list_controls` on an app whose UI changes
- `evaluate_script` that reads dynamic content
- Any MCP tool call whose output you need each turn

---

## How to use

- `create_daemon` with `daemon_action` = the full action dict to repeat.
- `unregister_daemon` with the daemon's `index` when you no longer need it.
- Daemon results appear each turn under **"Daemon Context — Current State"** as `Watcher N: ... State: ...`. This means: *no need to re-query* — the data is already here.

---

## Workflow

1. Identify a tool you'd call every turn anyway.
2. Create a daemon for it once.
3. Read the daemon's output from context each turn.
4. Unregister when done.
