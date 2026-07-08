# Skills

## WHAT A SKILL IS

Pre-tested procedure for a known task, provisioned via `skill_installation` mode. Replaces UI-hunting/ad-hoc Python with a known-good path. Ranked #2 in Core's Interaction Layer Priority — below MCP, co-equal with Python. Never use `python` for filesystem/clipboard/browser ops a skill covers.

---

## INVOKING

Each installed skill registers its own action names. The action to call will be specified in the task — use that action name directly. No generic `skill_action` wrapper.

```json
{"action": "<action_name>", "<param>": "<value>", "history": "string"}
```

---

## SCHEMA

```json
{"action": "install_skills", "skills": ["string"], "history": "string"}
```

Hands off to `skill_installation` mode to provision, then returns control.

---

## CONSTRAINTS

- Follow the skill's own steps — don't reimplement via another layer.
- Request only skills relevant to the current step.
- No match → next layer per Core's Interaction Layer Priority.
