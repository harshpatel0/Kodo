# Daemons (single source of truth for the Daemon task category)

Polling/monitoring/refreshing steps a daemon handles instead of you re-calling them every turn. Runs the tool call on your behalf and injects fresh results into context — costs you no action.

## SCHEMAS

```json
{"action": "create_daemon", "daemon_action": {...}, "history": "string"}
{"action": "unregister_daemon", "index": int, "history": "string"}
```

## When to daemonise

Any action you would manually re-call each turn — keeping a snapshot fresh, monitoring controls, checking dynamic content.

## How to use

1. `create_daemon` with `daemon_action` = the action dict to repeat. Runs every turn on your behalf.
2. Read its output from the Daemon Context each turn — do not re-call it yourself.
3. `unregister_daemon` with its `index` once stale/no longer needed.

```json
{"action": "create_daemon", "daemon_action": {"action": "list_controls"}, "history": "Watching for search results to populate instead of polling manually"}
{"action": "unregister_daemon", "index": 0, "history": "Results loaded, watcher no longer needed"}
```

Common candidates: `list_controls` while waiting for a Direct App Control list/tree to populate or refresh, `list_processes` while waiting for an app to launch, any `mcp_tool_call` that just checks status.
