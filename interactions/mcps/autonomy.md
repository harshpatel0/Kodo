# MCPs — Autonomy Mode

Calls external MCP tool servers for app-specific actions beyond OS control. Use when the task needs a defined tool/API, not raw window control.

Confirm tool name + arg schema from the server's registered list before calling — never guess.

## SCHEMA
```json
{"action": "mcp_tool_call", "tool": "string", "arguments": {}, "history": "string"}
```

## ISOLATION — HARD RULE
Once an MCP tool claims a resource (browser tab, app instance, connection), that resource is MCP-only for the rest of the sub-task. No DAC, pc_actions, or skills may touch it — even to "check state" or click something.

**Why:** MCP-managed resources aren't guaranteed to match what other layers see. DAC's `list_processes` may find a different process than the one MCP opened, or fight the MCP server for control — causing duplicate/conflicting actions. This risk is real for MCPs with multiple overlapping tools (nav + click + type, etc.); narrow single-purpose MCPs (e.g. a lookup tool) don't have this failure mode since there's no second path to reach for.

**Concrete failure:** MCP opens Chrome → next step needs a click → wrong: DAC `connect` into that Chrome. Right: use that same MCP server's click/nav tool.

**No equivalent tool exists for the step?** Emit `stuck` naming the gap. Don't improvise a cross-layer reach-in.

## CONSTRAINTS
- Only call registered/connected tools this session.
- Match arguments exactly to schema.
- Treat returned result as current state for next turn.
- Isolation ends when the sub-task's resource is released (closed, or task done).