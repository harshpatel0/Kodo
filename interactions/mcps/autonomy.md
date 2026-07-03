# MCPs — Autonomy Mode

Calls external MCP tool servers for app-specific actions beyond OS-level control (e.g. browser automation, package management, other connected services). Use when the task needs a defined tool/API rather than "control a visible OS window."

Each connected server exposes its own tool names and argument schemas at connection time. Confirm the exact tool name and required arguments from the server's registered tool list before calling — do not guess.

---

## SCHEMA
```json
{"action": "mcp_tool_call", "tool": "string", "arguments": {}, "history": "string"}
```

---

## CONSTRAINTS
- Only call tools actually registered/connected this session.
- Match `arguments` exactly to the tool's declared schema.
- Treat the returned result as current state for the next turn's verification step.