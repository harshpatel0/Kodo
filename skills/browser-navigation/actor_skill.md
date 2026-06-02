# Browser Navigation — Actor Guide

---

## PRIORITY RULES (Read First)

### 1 — Search Box Priority
When already on a website, ALWAYS use the site's own search box. NEVER use the browser address bar for on-site search.

| Situation | Use |
|---|---|
| Already on the site (YouTube, GitHub, etc.) | Site search box |
| Navigating to a new URL | Address bar (Ctrl+L) or `open_url` |

The new-tab page search widget (Bing/Google widget) is a trap — ignore it.

### 2 — Site vs Address Bar
- YouTube search: press `/` to focus the search box
- GitHub search: press `/` to focus the search box
- Address bar: `Ctrl+L` — only for new URLs

### 3 — Back and Forward Buttons
The browser has Back and Forward buttons in the accessibility tree. USE THEM.
- Made a mistake or landed on the wrong page? Click the **Back button** or press `Alt+Left`.
- Need to go forward? Click the **Forward button** or press `Alt+Right`.
- Prefer this over re-typing URLs. It is faster and safer.

---

## URL NAVIGATION

Prefer `open_url` for all URL navigation:
```json
{"action": "open_url", "url": "https://example.com"}
```

Manual fallback only if `open_url` is unavailable:
1. `press_hotkey ctrl+t` — new tab if needed
2. `press_hotkey ctrl+l` — focus address bar
3. type the URL
4. `press_key enter`

Before typing a URL, check the address bar. If the old URL is still visible and not highlighted, clear it first. This prevents malformed URLs like `youtube.comhttps://`.

---

## PAYWALLED OR SIGN-IN REQUIRED CONTENT

### Paywalls (payment required)
- If a page requires payment to proceed, STOP immediately.
- Do NOT enter any payment details under any circumstances.
- Emit `done` with a message: "Page requires payment. Stopping."
- Go back using the Back button or `Alt+Left`.

### Sign-In Walls
Only attempt sign-in if one of these is true:
- The task instruction explicitly provides credentials to use.
- The task instruction explicitly says to use browser-saved or password manager credentials.

If neither is true:
- Do NOT attempt to sign in.
- Do NOT guess or try saved credentials on your own.
- Press `Alt+Left` or click Back to return to the previous page.
- Continue the task without that content, or report that sign-in is required.

---

## WRONG PAGE RECOVERY

1. Press `Alt+Left` or click the Back button first — fastest recovery.
2. If Back does not help, use `open_url` with the correct URL.
3. If on Bing or Google search when the task targets YouTube, go directly to `https://youtube.com` via `open_url`.

Never declare stuck because you landed on the wrong page.

---

## TASK COMPLETION

### Video tasks
- Seeing a video in search results is NOT done.
- Done = the video watch page is loaded and the player is visible.
- Click the video title or thumbnail, then confirm the watch page loaded.

### Page/link tasks
- Done = the target page is fully loaded as the active window.

### Shop item
- Navigate to the product page directly.
- STOP if a checkout or payment page appears.

### Form
- Fill using user-provided info or browser autofill if available.
- STOP if payment details are required.

---

## TYPE AND SUBMIT

- The `type` action submits automatically.
- If the page does not change after typing, re-focus the input and retype.
- Do NOT click Refresh.
- If typing fails three times: press `/` (site search) or `Ctrl+L` (address bar) and retry.

---

## RESULT MATCHING

When a step says "title contains [X]":
1. Check the accessibility tree for an element whose name contains [X].
2. Scroll if not visible.
3. Only click if the name matches. Never click a non-matching element.