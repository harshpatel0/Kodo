## Watchdogs

Watchdogs allow you to send a `read_only` action for Kodo to watch it for you, when it changes or the timeout expires, it will automatically return the result. Use this when you want to be alerted when something changes without calling the same action.

``` json
{"action": "watchdog", "watchdog_action": {"action": "...", "..."}, "timeout": "...","history": "string"}
```

The default `timeout` is `15`.

### Constraints

Do not use Watchdogs when the action changes state, do not put `pc_actions` or `direct_app_control` actions into the Watchdog.
The exceptions to the `direct_app_control` actions are `list_processes` and `list_controls`, as these are read only actions.
Do not put a skill that changes the PC state, and for skills, always trust their watchdog protocols, some skills may already implement actions that wait for the action to complete before restoring control back to you, such as the built-in `launch_windows_app`.

**You must absolutely trust watchdog results.** When a watchdog returns, the watched condition has been met or timed out. Do NOT re-query the same tool to "confirm" — the watchdog result IS the confirmation. Kodo is helping you, not working against you. If an action is already being handled on your behalf (by a daemon, watchdog, or skill protocol), you do NOT need to run it yourself.

`clipboard_read` - Okay to watch, as it is a read-only process
`open_app` from `launch_windows_app` - Not okay, changes PC state (Launches an app) and has it's own Watchdog protocols
