# Microsoft Word — Actor Guide

Three phases must complete in order before emitting `done`:
1. **Write** — all content typed in full
2. **Format** — heading styles applied via Apply Styles dialog
3. **Save** — title bar confirms saved filename, not `Document1`

---

## Opening a Document

Word opens to a Start screen, not a blank document.

- **New:** Click `Blank document`, or `ctrl + n` if Word is already open
- **Existing:** Click `Open` or `ctrl + o`, navigate to file

Before typing, confirm `Edit | name='Page 1 content'` is in the UIA tree. If absent, you are still on the Start screen. After `ctrl + n`, click the document center if this node does not appear automatically.

---

## Typing Content

Press `ctrl + end` before typing to anchor the cursor at the document end.

- Use `\n` for a line break, `\n\n` for a new paragraph
- Write all content in one pass — do not stop to format mid-document
- Do not use markdown syntax (`#`, `**`, `*`) — Word renders these as literal characters

**Gotchas:**
- **Cursor unknown:** If you have not pressed `ctrl + end`, you do not know where the cursor is. Always anchor first.
- **Autocorrect:** `--` becomes em dash, `(c)` becomes ©. If unexpected characters appear, press `ctrl + z` once immediately.
- **Auto list:** A line starting with `1.` or `-` may trigger list mode. Press `ctrl + z` once to remove it — text is preserved.
- **Mini toolbar trap:** If text is selected, Word shows a floating toolbar. Typing while it is visible sends keystrokes to the Font Search Box, not the document. If `Bold`, `Italic`, or `Font Color` appear near your coordinates, press `right` to dismiss the selection first.
- **Duplicate content:** Press `ctrl + a`, `backspace` to clear, then re-anchor with `ctrl + end` and retype. Do not attempt to delete mid-paragraph.
- **UIA truncation:** The tree truncates long text nodes. Scroll to verify content end after large blocks — do not assume the full text landed correctly.

---

## Applying Heading Styles

Apply styles only after all content is written. Use the Apply Styles dialog (`ctrl + shift + s`) exclusively — do not use the ribbon or styles panel.

**Order of application (top to bottom):**
1. `Title` — once, at the very top
2. `Heading 1` — major sections
3. `Heading 2` — subsections
4. `Heading 3` — sub-subsections

**Sequence per heading:**
1. Press `ctrl + home` before the first heading to anchor at document top
2. `ctrl + f` → search for the heading text → `enter` → `esc`
3. Verify the UIA tree shows the cursor on the correct line
4. `ctrl + shift + s` → Apply Styles dialog opens (ComboBox or Edit field visible)
5. `ctrl + a` to clear the field → type the exact style name (capitalisation matters)
6. `enter` to apply — dialog stays open, do not close it
7. Re-read the UIA tree to confirm the style applied correctly
8. Repeat from step 2 for the next heading

**Gotchas:**
- **Dialog not opening:** Document body lost focus. Click the document center, confirm `Edit | name='Page 1 content'` is present, then retry.
- **Style field not clearing:** Click the ComboBox directly in the UIA tree to focus it, then `ctrl + a`.
- **Wrong line:** Style applies to the line the cursor is on. Always use `ctrl + f` to position first.
- **Find wraps:** If the cursor jumps unexpectedly, Find wrapped to document start. Press `ctrl + home` and search again.
- **Coordinate shift:** Applying a style shifts `y` coordinates of all content below it. Never reuse coordinates after a style application — re-read the tree.

**Bullet lists:** Do not type `-` to create bullets. Type only the first bullet line, then press `enter` for each subsequent item. If dashes were typed during writing, remove them and convert to proper Word bullet formatting.

**Style correction:** While formatting, fix issues as encountered — missing titles, malformed headings, inconsistent paragraph breaks. Do not defer corrections.

---

## Saving

Use the File menu, not `ctrl + s`.

1. Click `Button | name='File Tab'`
2. Click `Save` or `Save As` from the UIA tree
3. If first save, a Save As dialog opens — fill filename if needed, click `Button | name='Save'`
4. After saving, verify the title bar shows the saved filename with no unsaved indicator

**Gotchas:**
- **First save:** Clicking `Save` on an unsaved document opens Save As regardless.
- **OneDrive default:** Save As may default to OneDrive. Navigate to the correct local folder before saving if required.
- **File menu stays open:** Press `esc` if the document body is not visible after saving.