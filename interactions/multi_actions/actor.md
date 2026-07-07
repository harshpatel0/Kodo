---

## BATCHING ACTIONS
Output a JSON array `[...]` to execute multiple actions in a single turn. Use batching ONLY when:
- You are confident every action will succeed — same tool, same conditions, only a parameter changes.
- The actions are **independent** or have a **deterministic outcome** — intermediate state changes won't cause a later action to fail.
- You can tolerate all actions executing without your oversight — once a batch starts, you do not regain control until every action completes.

**Do NOT batch** when:
- An action's success is uncertain and later actions depend on it.
- State may change unexpectedly (e.g. navigating between pages, waiting for loading).
- The batch would be longer than ~5 actions — keep batches short so you can react to surprises.

Each action in the array follows the same schemas below. Every action must still include a `history` field.

---