import sys
import json
import subprocess


def clipboard_write(text: str) -> None:
    """Write text to the Windows clipboard using clip.exe (no dependencies)."""
    try:
        subprocess.run(
            ["clip"],
            input=text,
            text=True,
            encoding="utf-8",
            check=True,
        )
        print(f"Clipboard written: {text[:80]}{'...' if len(text) > 80 else ''}")
    except Exception as e:
        print(f"Failed to write clipboard: {e}", file=sys.stderr)


def clipboard_read() -> None:
    """Read text from the Windows clipboard via PowerShell."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=True,
        )
        content = result.stdout.strip()
        if content:
            print(content)
        else:
            print("[Clipboard is empty]")
    except Exception as e:
        print(f"Failed to read clipboard: {e}", file=sys.stderr)


if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    action = args.get("action")

    if action == "clipboard_write":
        clipboard_write(args["text"])
    elif action == "clipboard_read":
        clipboard_read()
    else:
        print(f"Invalid Action {action}")
