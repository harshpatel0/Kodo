# Python

Runs arbitrary Python for computation/logic/data manipulation uncovered by other layers. Ranked #3 in Core's Interaction Layer Priority.

---

## SCHEMA

```json
{"action": "python", "code": "string", "history": "string"}
```

---

## CONSTRAINTS

- Co-equal with skills: use skill if one directly matches; Python only for uncovered steps.
- Not a UI substitute — no simulated clicks/typing (DAC/PC Actions job).
- Complete, runnable code only — no stubs/placeholders.
