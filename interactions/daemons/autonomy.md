# Daemon Actions

Daemons are not actions themselves — they are persistent watchers that run every step and inject their results into context. Use daemons as an extension to the context provider when you need to observe something that changes constantly: live clock, clipboard state, network status, file watchers, Minecraft server chat (via MCP), etc. Register once and the output appears in the prompt each turn automatically.

Daemons **do** have side effects: the `daemon_action` is dispatched through `parse_action` each step, so if you daemonize an `mcp_tool_call`, that tool is actually called every turn. Don't daemonize mutating actions.

## SCHEMAS

```json
{"action": "create_daemon", "daemon_action": {"action": "...", ...}, "history": "string"}
{"action": "unregister_daemon", "index": int, "history": "string"}
```

- `daemon_action`: any valid action (`python`, `mcp_tool_call`, etc.). Runs every step. **Do not use `pc_actions` (click, type, etc.) or `direct_app_control` actions** — those would execute every turn, not observe.
- `index`: which daemon to remove (0-based, shown in the Daemon Result header).

## CONSTRAINTS

- **Observation only:** daemons gather context, they do not drive workflow. Use the action pipeline for execution.
- **Trust daemon results** the same as your own actions — they run every turn and inject fresh context. Never re-query daemonized tools.
- **History is you.** Each turn you see what *you* did before. If a directive or past action already set a plan, follow it — don't recreate it. You are not a new agent each turn; you are the same agent continuing your work. Stop planning and start doing.
- **Side effects are real:** each daemon calls `parse_action` every step. Daemonizing a `pc_actions` action like `click` means clicking the exact same spot every single turn. Never daemonize anything that mutates state — it will repeat endlessly.
- **Keep it light:** daemons run synchronously. Heavy ones slow every step.
- **Daemons are auto-cleaned.** When you emit `done`, remaining daemons are unregistered automatically. Do NOT manually unregister daemons — never use `unregister_daemon` in your actions. The system handles cleanup.
- **Do not use daemons to watch `direct_app_control` controls.** There is already a user setting (`settings.direct_app_control.always_populate_connected_app_controls`) that injects controls into context automatically. If you create a daemon that calls `direct_app_control` actions, it will observe the **same already-connected window** — it cannot watch a different window than the one already connected.
