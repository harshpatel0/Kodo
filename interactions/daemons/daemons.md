# Daemon Layer

Daemons run a tool call every turn on your behalf and inject fresh results into context. You do not spend an action on it.

---

## SCHEMAS

```json
{"action": "create_daemon", "daemon_action": {...}, "history": "string"}
{"action": "unregister_daemon", "index": int, "history": "string"}
```

---

## When to daemonise

Any action you would manually re-call each turn — keeping a snapshot fresh, monitoring controls, checking dynamic content.

---

## How to use

- `create_daemon` with `daemon_action` = the action dict to repeat.
- `unregister_daemon` with the daemon's `index` when done.
- Results appear each turn as daemon context. Do not re-query.

---

## Workflow

1. Spot a tool you would re-call every turn.
2. Daemonise it once.
3. Read its output from context.
4. Unregister when stale.
