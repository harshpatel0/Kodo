# Contributing to Kodo

Basic guide for submitting changes.

---

## Responsibility

You are responsible for every line in your PR, regardless of how it was written. AI-assisted code is fine, but if it breaks something that is on you to fix, not the tool that generated it. "My AI did it" is not a valid response to a bug report. Review what you submit, make sure it integrates cleanly with the rest of the codebase, and be prepared to own it after it merges.

---

## Before You Start

- Check open issues and PRs first so you're not duplicating something already in progress.
- For bigger changes (new orchestrator modes, provider backends, architectural stuff), open an issue first so we can talk about it before you write the code.
- Kodo is MPL-2.0. Submitting a PR means your contribution is under the same license.

---

## Pull Request Format

### Title

Use the format: `[type] Short description`

| Type | When to use |
|---|---|
| `feat` | New functionality (new skill, new provider, new action type) |
| `fix` | Bug fix |
| `refactor` | Code restructure with no behaviour change |
| `docs` | Documentation only (README, AGENTS.md, skill guides, comments) |
| `skill` | New or updated skill in `skills/` |
| `settings` | Changes to settings schema or defaults |
| `chore` | Dependency updates, gitignore, tooling |

Examples:
- `[feat] Add DeepSeek provider`
- `[skill] Add clipboard skill`
- `[fix] skill_orchestrator double-instantiation on parse_action import`

---

### Description

Three sections, keep them short:

#### What does this change do?
What it does and why. A sentence or two is fine for small changes.

#### Type of change
Tick whichever apply:

- [ ] New feature
- [ ] Bug fix
- [ ] Refactor / cleanup
- [ ] Documentation
- [ ] New skill
- [ ] Breaking change (existing behaviour changes or settings schema changes)

#### Files changed
One line per file, say what changed in it.

```
models/provider/deepseek_provider.py  - new DeepSeek provider implementation
models/provider/__init__.py           - registered DeepSeek in the factory map
settings/default.py                   - added deepseek block to model_providers defaults
docs/MODEL_PROVIDERS.md               - added DeepSeek setup section
```

---

## Skills

Skills are not accepted into the main repo unless they work correctly on any Windows machine with no assumptions about what software is installed. System-specific skills (personal workflows, specific tools, specific apps) belong in your own repo. `skills/AGENTS.md` has everything you need to build one.

If you think a skill clears that bar, open an issue to discuss before submitting.

---

## Code Style

- Match the style of the file you're editing.
- Settings are always read from the `settings` singleton in `settings/settings.py`, never hardcoded.
- New providers must implement `ModelProvider.chat()` from `models/provider/base.py` and be registered in `models/provider/__init__.py`. Nothing else should need to change.

---

## What Makes a Good PR

- One concern per PR. A skill + a provider + a bug fix together is hard to review.
- Should not depend on another unmerged PR unless clearly noted.
- If you add a setting, add it to the README settings table. If you add a skill action, document it in the skill's `.md` files. If you change the provider interface, update `docs/MODEL_PROVIDERS.md`.
