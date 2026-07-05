# Skills — Autonomy Mode

## WHAT A SKILL IS
Pre-tested procedure for a known task, provisioned via `skill_installation` mode. Replaces UI-hunting/ad-hoc Python with a known-good path. Priority: below MCPs, co-equal with Python — use if one matches the step. Never use `python` for filesystem/clipboard/browser ops a skill covers.

## INVOKING
``` json
{"action": "skill_action", "param": "value", "history": "string"}
```
Replaces any other layer's action when a matching skill is installed.

## SCHEMA
```json
{"action": "install_skills", "skills": ["string"], "history": "string"}
```
Hands off to `skill_installation` mode to provision, then returns control.

## CONSTRAINTS
- Follow the skill's own steps — don't reimplement via another layer.
- Request only skills relevant to the current step.
- No match → next layer: MCPs → Skills/Python → DAC → PC Actions.