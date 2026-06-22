# Python Engine — Planner Guide

## When to Use
Use `python` for process launching, system queries, data transformation, calculations, or anything faster in code than via UI. Do NOT use if a loaded skill or accessibility tree action can do it.

## Action Format
```
instruction: "python | code=import subprocess; subprocess.Popen(['notepad.exe'])"
expected_result: "[Verifiable system state — not script output. E.g. 'Notepad is the active foreground window']"
fallback: "[UI-based alternative using click/type/hotkey]"
```

## Rules
- Write actual executable code in the instruction — never describe what it should do
- Chain multiple statements with semicolons on one line
- `expected_result` must describe a visible system state, not what the script prints
- Every python step requires a UI-based fallback
- No blocking code — no `input()`, no infinite loops