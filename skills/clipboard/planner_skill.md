# Clipboard — Planner Guide

## clipboard_write

Write text into the Windows clipboard so the user can paste it elsewhere.

```
instruction: "clipboard_write | text=<<text to copy>>"
"expected_result": "The text is placed on the clipboard"
"fallback": "Use a Python code action to write to the clipboard via pywin32"
```

## clipboard_read

Read the current text contents of the Windows clipboard.

```
instruction: "clipboard_read"
"expected_result": "The clipboard content is returned to the user"
"fallback": "Use a Python code action to read the clipboard via pywin32"
```
