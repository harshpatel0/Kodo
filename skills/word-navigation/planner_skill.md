# Microsoft Word — Planner Guide

All Word tasks require three phases in this order. Do not plan `done` until all three are complete.

**Phase 1 — Write:** Type all content before touching any formatting.
**Phase 2 — Format:** Apply heading styles using the Apply Styles dialog (`ctrl + shift + s`).
**Phase 3 — Save:** Save via the File menu. Confirm the title bar shows the saved filename.

---

## Planning Rules

- Always plan a `ctrl + end` step before any typing to anchor the cursor
- Always plan a `ctrl + home` step before the formatting phase begins
- Separate writing and formatting into distinct plan phases — never interleave them
- Never plan markdown syntax (`#`, `**`) — Word renders these as literal characters
- Plan one heading style application per step — do not batch them

---

## Action Formats

### Open or create a document
```
instruction: "Click 'Blank document' on the Word Start screen"
expected_result: "Edit | name='Page 1 content' is present in the UIA tree"
fallback: "Press ctrl + n if Word is already open and the Start screen is not visible"
```

### Type content
```
instruction: "Press ctrl + end to anchor cursor, then type [content]"
expected_result: "Text appears in the document body"
fallback: "Click the center of the document area to focus it, then retry ctrl + end"
```

### Apply a heading style
```
instruction: "Use ctrl + f to locate '[heading text]', then apply '[Style Name]' via ctrl + shift + s"
expected_result: "The heading line reflects the applied style in the UIA tree"
fallback: "Click the document body to restore focus, then retry ctrl + shift + s"
```

### Save the document
```
instruction: "Click File Tab, then click Save or Save As"
expected_result: "Title bar shows the saved filename with no unsaved indicator"
fallback: "If the File menu remains open, press Escape, then retry"
```