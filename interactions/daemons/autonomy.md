## DAEMON WATCHERS
Daemons run a tool call every turn on your behalf and inject fresh results into context. You don't spend an action on it.

### When to daemonise
Any action you'd manually re-call each turn — keeping a snapshot fresh, monitoring controls, checking dynamic content.

### How to use
- `create_daemon` with `daemon_action` = the action dict to repeat.
- `unregister_daemon` with the daemon's `index` when done.
- Results appear each turn as daemon context. Don't re-query.

### Workflow
1. Spot a tool you'd re-call every turn.
2. Daemonise it once.
3. Read its output from context.
4. Unregister when stale.
