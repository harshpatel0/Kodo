# Python — Autonomy Mode

Executes arbitrary Python for computation, logic, or data manipulation that no other layer directly covers.

---

## SCHEMA
```json
{"action": "python", "code": "string", "history": "string"}
```

---

## CONSTRAINTS
- **Skill priority:** If `skills` is active and an installed skill covers this step (filesystem, clipboard, browser, or other packaged operation), use the skill instead of ad-hoc Python.
- **Not a UI substitute:** Don't use `python` to simulate clicking/typing into an app — that's `direct_app_control` or `pc_actions`' job.
- **Full output:** Code must be complete and runnable, no placeholders or stubs.