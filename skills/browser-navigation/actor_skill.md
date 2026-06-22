# Browser Navigation — Actor Guide

Navigates URLs, searches sites, and retrieves web content.

## URL Navigation

Prefer `open_url`:

```json
{"action": "open_url", "url": "https://example.com"}
```

Fallback: `Ctrl+T` (new tab), `Ctrl+L` (address bar), type URL, `Enter`.

## Site Search vs Address Bar

- **Already on the site** (YouTube, GitHub) → use site's search box (press `/` to focus)
- **New URL** → use address bar (`Ctrl+L`) or `open_url`

## Error Recovery

Wrong page? Click the Back button or press `Alt+Left`. Re-navigate if needed.

## Paywalls & Sign-In

- **Paywall** → Stop. Do not enter payment details. Go back.
- **Sign-in** → Only proceed if: (1) credentials are provided in the task, (2) allowed to use saved credentials from password manager, or (3) instructed in the user's extra instructions field. Otherwise go back.

## Result Matching

When clicking a search result: find the element in the tree whose name most closely matches what the user typed or requested. Scroll if not visible. Click the most relevant match.

## Task Completion

- **Video** → Done when watch page is loaded and player is visible (not just in search results)
- **Page/link** → Done when the target page is fully loaded
- **Shop item** → Stop before checkout page