import webbrowser
import sys
import json

# Set Opening Mode to existing, tab, or window to open the url in a existing browser window, a tab in the existing window, or just a new window
OPEN_MODE = "window"


def open_url(url: str) -> None:
    webbrowser_opening_mode = 1

    url = url.strip()

    if OPEN_MODE == "existing":
        webbrowser_opening_mode = 0
    if OPEN_MODE == "tab":
        webbrowser_opening_mode = 2
    if OPEN_MODE == "window":
        webbrowser_opening_mode = 1

    if not url.lower().startswith(("http://", "https://")):
        url = "http://" + url

    webbrowser.open(url=url, new=webbrowser_opening_mode)


if __name__ == "__main__":
    # Args passed as JSON via environment or stdin
    args = json.loads(sys.argv[1])
    open_url(args.get("url"))
