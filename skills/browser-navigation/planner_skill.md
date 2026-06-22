# Browser Navigation — Planner Guide

## open_url

Always prefer `open_url` over manual navigation steps. Only fall back to manual if the skill is not loaded.

```
instruction: "open_url | url=https://www.example.com"
expected_result: "The page is fully loaded as the active browser tab"
fallback: "Press Ctrl+T to open a new tab, Ctrl+L to focus the address bar, type the URL, press Enter"
```

## Search Flows

Split search tasks into atomic steps — never combine navigation and result-clicking into one step:

1. `open_url` to the site
2. Confirm site loaded (expected_result of step 1)
3. Type query into the site's search input
4. Press Enter
5. Click the result whose title most closely matches the query
6. Confirm the target page is the active view

Step 5 instruction format:
```
instruction: "Click the search result whose title most closely matches '<<query>>'"
expected_result: "The target page is loaded and its primary content is the active view"
fallback: "If no close match is visible, scroll down and re-evaluate results"
```

## Expected Results for Navigation Steps

Must describe arrival at the destination — not the action taken.

- WRONG: `"The link was clicked"`
- WRONG: `"The video appears in search results"`
- RIGHT: `"The video watch page is loaded and the media player is visible as the active content"`

## Tab Safety

Never navigate an existing tab unless the task explicitly requires modifying the current page. Always plan an `open_url` or new tab step first.