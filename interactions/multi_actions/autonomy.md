## Task Structure: Parallel Category (single source of truth for this category)

This layer adds a **Parallel** category to task decomposition: steps that can run alongside other work in the same turn, emitted as a JSON array instead of one action at a time.

---

## BATCHING ACTIONS
Output a JSON array `[...]` to execute multiple actions in a single turn. Use batching ONLY when:
- You are confident every action will succeed — same tool, same conditions, only a parameter changes (e.g. dig a line of blocks, fill multiple form fields, click a series of buttons).
- The actions are **independent** or have a **deterministic outcome** — intermediate state changes won't cause a later action to fail. This includes short dependent chains where an earlier action's effect is predictable enough that you don't need to re-verify it before the next one — e.g. clicking a text field then immediately typing into it, when nothing else in the tree could plausibly steal focus.
- You can tolerate all actions executing without your oversight — once a batch starts, you do not regain control until every action completes.

**Do NOT batch** when:
- An action's success is uncertain and later actions depend on it.
- State may change unexpectedly (e.g. navigating between pages, waiting for loading).
- The batch would be longer than ~5 actions — keep batches short so you can react to surprises.

Each action in the array follows the same schemas as a single action. Every action must still include a `history` field.

```json
[
  {"action": "mcp_tool_call", "tool": "dig-block", "arguments": {"x": 100, "y": 64, "z": 200}, "history": "Dug bottom log"},
  {"action": "mcp_tool_call", "tool": "dig-block", "arguments": {"x": 100, "y": 65, "z": 200}, "history": "Dug middle log"},
  {"action": "mcp_tool_call", "tool": "dig-block", "arguments": {"x": 100, "y": 66, "z": 200}, "history": "Dug top log"}
]
```
