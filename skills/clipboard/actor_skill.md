# Clipboard — Actor Guide

Provides read/write access to the Windows clipboard.

## Actions

### clipboard_write

Writes text to the Windows clipboard (replaces any existing content).

```json
{"action": "clipboard_write", "text": "Text to copy to clipboard"}
```

- `text` (required) — The string to place on the clipboard.

### clipboard_read

Returns the current text content of the Windows clipboard.

```json
{"action": "clipboard_read"}
```

No parameters. Returns the clipboard text as output, or `[Clipboard is empty]` if nothing is on the clipboard.

## Notes

- Uses `clip.exe` for writing and PowerShell `Get-Clipboard` for reading — no external dependencies.
- Only text content is supported. Images or other clipboard formats cannot be read/written.
