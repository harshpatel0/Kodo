# Skills — Autonomy Mode

## WHAT A SKILL IS
A skill is a pre-packaged, pre-tested procedure for a known task or app operation, provisioned into the session by the `skill_installation` mode. Skills exist to replace ad-hoc discovery (UI hunting, hand-written Python) with a known-good path. Highest priority layer: if an installed skill covers the current step, use it instead of `direct_app_control`, `mcps`, `pc_actions`, or `python`. Never use `python` for filesystem, clipboard, or browser operations a skill already covers.

## INVOKING AN INSTALLED SKILL
Once installed, a skill is invoked as an action in the format:
```
skill-name | param=value
```
Use this whenever a matching installed skill exists for the current step, in place of any other layer's action.

Example — `textbox-input` (used to hand control back to the user):
```json
{"action": "textbox-input", "title": "Need login credentials", "body": "Please enter your account password to continue", "history": "Skill textbox-input invoked; task requires user-supplied credentials not available to Kodo"}
```

---

## SCHEMA
```json
{"action": "install_skills", "skills": ["string"], "history": "string"}
```
Emitting this hands control to the `skill_installation` mode, which selects and provisions the relevant skill(s), then returns control to autonomy with the skill's instructions available.

---

## CONSTRAINTS
- Once a skill is installed, follow its own documented steps/entry points rather than reimplementing the procedure with another layer.
- Only request skills relevant to the current step.
- If no installed skill covers the step, fall through to the next layer per priority order (`direct_app_control` → `mcps` → `pc_actions` → `python`).