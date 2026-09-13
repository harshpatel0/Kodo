## Task Structure: Daemon Category (single source of truth for this category)

This layer adds a **Daemon** category to task decomposition: polling, monitoring, or refreshing steps that a background daemon handles instead of you calling them manually every turn.

---

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

---

## EXAMPLES

```json
{"action": "create_daemon", "daemon_action": {"action": "list_controls"}, "history": "Watching for search results to populate instead of polling manually"}
{"action": "unregister_daemon", "index": 0, "history": "Results loaded, watcher no longer needed"}
```

Common candidates: `list_controls` while waiting for a Direct App Control list/tree to populate or refresh, `list_processes` while waiting for an app to launch, any `mcp_tool_call` that just checks status.
