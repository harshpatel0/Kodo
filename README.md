# Kodo (previously called LMControl)

Kodo lets a local LLM take control of your Windows PC. It reads the live accessibility tree, reasons about what's on screen, and emits actions until the task is done. Clicks, keystrokes, file writes, code execution, whatever it takes. It runs entirely on your machine through [Ollama](https://ollama.com) if you choose to do so, so nothing leaves your computer.

**It's not a polished product. It's a project that works well enough to be genuinely useful, built to see how far local models can go on real desktop tasks. Models get confused, occasionally do something baffling, and need hand-holding on complex apps. The architecture is designed to recover when that happens rather than just die.**
**Expect crashes and unexpected behaviour**

**Windows only.** The UI layer is built on pywinauto and the Windows UIA accessibility tree. macOS and Linux are not supported.

**A note on the code.** The core logic and architecture are handwritten, with system prompts and user prompts being fully AI geneated. AI was also useful as a sounding board during design, helped write some of the smaller utility functions, and was involved in refactors and documentation (this README file). It's not vibe-coded, but it's not purely solo either.

## Security Disclaimer (very important!)

This is a project I started making on my own with no scope planning or safety design, and I'm not taking responsibility for what happens when you run it. Skills and the `python` action can execute arbitrary code on your machine. The venv isn't a sandbox, it's just there to keep packages off your native Python installation. 
**Prompt injection is a real risk** if the model ends up reading adversarial content mid-task. Be deliberate about what you feed it.

---

## Table of Contents

- [Installation](#installation)
- [Setup](#setup)
- [Running Kodo](#running-kodo)
- [Custom Instructions](#custom-instructions)
- [Autonomy Mode](#autonomy-mode)
- [Settings](#settings)
- [Model Recommendations](#model-recommendations)
- [Skills](#skills)
  - [Skill Types](#skill-types)
  - [Installing a Skill](#installing-a-skill)
  - [Creating a Skill](#creating-a-skill)
  - [skill.json Schema](#skilljson-schema)
- [Architecture](#architecture)

---

## Installation

### Automated Setup

```bash
git clone https://github.com/harshpatel0/Kodo.git
cd Kodo
py main.py
```

On first launch, you'll be taken through a setup wizard, follow the onscreen prompts to setup Kodo.
First launches will take longer as virtual environments and dependencies are installed, subsequent launches will not take as long.

### Manual Installation

```bash
git clone https://github.com/harshpatel0/Kodo.git
cd Kodo
pip install -r requirements.txt
```

You'll also need [Ollama](https://ollama.com) installed and at least one model pulled. More on that in [Model Recommendations](#model-recommendations).

---

## Setup

0. **Install Python Dependencies** by running `pip install -r requirements.txt` in the project's root folder.

1. **Install Ollama** and pull a model. `gemma4:e4b` is what this was built and tested on:

   ```bash
   ollama pull gemma4:e4b
   ```

2. **Start the Ollama server:**

   ```bash
   ollama serve
   ```

   By default it runs on `localhost:11434`. If you're hosting Ollama elsewhere, update `ollama_server` in `settings.json` after the first run.

3. Run `main.py` with a task and you're off.

> Ollama steps will only apply if you are using a local Ollama Model

---

## Running Kodo

### Using the Web API

Kodo exposes an API, make sure all dependencies are installed and then run the main `main.py` file.

> If the Live Desktop Preview does not show up, refresh the page.

### Directly

The main file accepts a `-t` flag, run

``` bash
py main.py -t your task here
```

e.g.,

``` bash
py main.py -t Send a Toast Notification with my current OS Version
```

This will run your task directly and quit once the LLM invokes the `done` action, using your settings.json file

### You can do this too, if you want to

Open `orchestrator.py` and set your task at the bottom of the file.

```python
if __name__ == "__main__":
    task = "Paste my clipboard contents to a file called clipboard_contents.txt, delete the old file if it exists"

    run_externally(task=task)
```

Then:

```bash
python orchestrator.py
```

Keep your mouse away from the top-left corner of the screen. That's the pyautogui failsafe and straying into that corner will immediately abort the run.
> You now also know what to do incase you want to stop it.

---

## Autonomy Mode

There's no upfront plan. The actor runs in a free loop, observing the UI state each turn, deciding what to do, and acting. It keeps a running `history` string across turns as its working memory.

Kodo used to also ship a Planner-Actor mode, where a separate Planner model produced a fixed JSON plan for an Actor to follow. It was dropped: real tasks drift from any plan made before execution starts, and reconciling that drift with a fixed checklist caused more confusion than it prevented. The actor deciding its own path as it goes, with no harness holding it to a stale plan, is the whole architecture now.

---

## Custom Instructions

Custom Instructions can be added to Kodo, in the `prompts/custom_instructions.md` file, these are additional instructions you would like Kodo to remember when performing a task, such as your name, your PC's username, PC's specs or how you would like Kodo to handle your tasks and use your skills.
Create the file and add in your custom instructions in Markdown format.

## In Practice

The models are inconsistent. That's just the reality of running small local models on tasks this complex. Sometimes a run goes flawlessly and you watch it open an app, navigate to the right page, and complete a multi-step task, and navigate around failures and unexpected behaviour. Other times it will do something so confidently wrong that you have to just sit back and appreciate it.

Some real examples from development:

**The Gemini incident.** The task was to open Gemini, write a comprehensive report on dinosaurs, and have Gemini proofread. The actor opened the browser, navigated to gemini.google.com, typed the task into the prompt box, and submitted it. Gemini responded with a report on dinosaurs. The actor looked at the screen, saw a report on dinosaurs, and emitted `done`. Its reasoning: *"looks like Gemini already generated a report on dinosaurs so I wouldn't need to."* It was technically correct. It was also completely wrong. Best and worst outcome simultaneously.

**Word, planner mode.** Same report task, but in Microsoft Word with the planner architecture. The actor successfully opened Word, typed out a full report, and called done. No heading styles applied. No save. Just raw text in an unsaved document and a very satisfied `done` signal. The word-navigation skill exists largely because of sessions like this.

The inconsistency is the main thing to be aware of going in. `action_settle_time`, iteration budgets, and the skill system all exist to give the model more chances to recover when it goes sideways. They help a lot, but they don't make the model reliable, they make unreliability survivable.
While on this topic, it is likely that Exceptions from invalid inputs are triggered, they sometimes happen and sometimes don't, so I am sure I haven't caught 99.9% of them.

---

### Settings

On first run, Kodo writes a `settings.json` to the project root using the defaults below. Edit it directly and restart.

```json
{
  "models": {
    "ollama_server": "localhost:11434",

    "skill_installation": {
      "model_name": "gemma4:e4b",
      "temperature": 0.1,
      "keep_alive": 0
    },

    "autonomy_actor": {
      "model_name": "gemma4:e4b",
      "thinking": true,
      "temperature": 0.5,
      "keep_alive": 150,
      "attach_screenshot_of_active_window": false
    }
  },
  "orchestrator": {
    "action_settle_time": 4,
    "max_replan_loop": 7,

    "autonomy_orchestrator": {
      "enforce_max_total_iterations": true,
      "max_total_iterations": 50
    }
  },
  "context_provider": {
    "waiting_period": 4,
    "skip_after_ticks": 10
  }
}
```

### Setting Reference

| Setting | Default | What it does |
|---|---|---|
| `models.ollama_server` | `localhost:11434` | Where to find the Ollama API. Change this if Ollama is running on a different machine or port. |
| `models.skill_installation.model_name` | `gemma4:e4b` | Model used for the pre-planning skill selection call. Can be a smaller/faster model since the task is just picking from a list. |
| `models.skill_installation.temperature` | `0.1` | Keep this low. Skill selection should be precise. |
| `models.skill_installation.keep_alive` | `0` | Skill installation runs once per task. No reason to keep it warm. |
| `models.autonomy_actor.model_name` | `gemma4:e4b` | Model that reads the UI tree and decides + executes each step, one action at a time. |
| `models.autonomy_actor.thinking` | `true` | Prepends `<\|think\|>` to the system prompt. **Gemma 4 models only.** See the warning in Model Recommendations. |
| `models.autonomy_actor.temperature` | `0.5` | Middle ground -- the autonomy actor is both deciding what to do and how to do it, so it needs some variety without being erratic. |
| `models.autonomy_actor.keep_alive` | `150` | Autonomy mode runs many iterations per task, so keeping the model loaded is worth it. |
| `models.autonomy_actor.attach_screenshot_of_active_window` | `false` | Attaches a JPEG screenshot of the active window to each turn. Only useful if your model has vision. |
| `orchestrator.action_settle_time` | `4` | Seconds to wait after each action before reading the UI tree again. Reduce this if your apps respond fast. Increase it if the actor keeps acting before the UI has caught up. |
| `orchestrator.max_replan_loop` | `7` | If the actor replans to the same instruction this many times in a row, it's flagged as a loop and the run is killed. |
| `orchestrator.autonomy_orchestrator.enforce_max_total_iterations` | `true` | Set to `false` to let Autonomy mode run without a turn limit. Only do this if you're watching it. |
| `orchestrator.autonomy_orchestrator.max_total_iterations` | `50` | Hard cap on how many turns `AutonomyOrchestrator` can run. Ignored if `enforce_max_total_iterations` is `false`. |
| `context_provider.waiting_period` | `4` | Consecutive stable ticks required before the UI tree is considered settled and ready to read. |
| `context_provider.skip_after_ticks` | `10` | Maximum ticks to wait before reading the tree anyway. Prevents the context provider from hanging on apps that never fully settle. |

### Recommended Temperature Settings

| Skill Installation | Autonomy Actor |
|---|---|
| 0.1 | 0.5 |

---

## Model Recommendations

Kodo was built on `gemma4:e4b` and that's still the recommendation. It handles structured JSON output well, follows long system prompts reliably, and the thinking mode gives it meaningfully better reasoning on UI tasks.

| Model | Verdict |
|---|---|
| `gemma4:e4b` | The primary dev target. Everything is tuned around this. |
| `qwen3:8b` | A solid alternative. Performs well in practice. Set `thinking: false`. |
| Larger models | Likely better. Largely untested. |
| Tiny models (1-3B) | Haven't tested these seriously. The concern is that the actor receives a large, dense context on every single call -- the full UI tree, task state, accumulated history, loaded skill docs, and system prompt all at once. Small models tend to get overwhelmed by that and lose track of what they're supposed to be doing. Worth experimenting with, but don't expect reliable results. |

**Thinking mode warning.** The `thinking` flag prepends `<|think|>` to the system prompt. This is a Gemma 4 feature. Enabling it on other models will not produce the intended effect and will likely corrupt JSON output formatting.

---

## Skills

Skills are how you extend Kodo beyond basic mouse and keyboard actions. A skill can give the actor step-by-step procedural guidance for a specific application, expose new callable actions the actor can emit, or both.

### Skill Types

#### Documentation Skills

Documentation skills teach the actor how to operate specific UI elements or complete specific tasks. They do not have any actions or functions assigned to them, just markdown files that get loaded into the actor's system prompt when the skill is selected.

`word-navigation` is the main example. It gives the actor a full procedural guide for Microsoft Word's UIA tree, covering the Apply Styles dialog, cursor anchoring, heading application order, save flows, and every gotcha that would otherwise cause a stuck loop. Without it the actor is guessing.

`python` documents the built-in `python` action, covering when to use code over UI interaction, the expected format, constraints, and how output comes back to the orchestrator.

#### Static Skills

Have a Python entry point and register named actions the actor can emit directly. Documentation lives in a static `actor_skill.md` file that is loaded once and injected as-is.

`browser-navigation` and `toast-notifications` are both static skills.

```json
{"action": "open_url", "url": "https://youtube.com"}
{"action": "send_toast", "title": "Done", "body": "Task complete"}
```

When the actor emits a registered action name, the skill orchestrator intercepts it and runs the entry point with the action's arguments passed as JSON.

#### Dynamic Skills

The entry point runs with a `--generate` flag at load time and produces documentation as a JSON string rather than reading from static files. The skill generates its own context based on the current system state.

`launch-windows-app` is the example here. It scans the Start Menu at runtime to find every installed `.lnk` shortcut, then injects the real list of launchable apps into the actor's prompt. The model always sees your actual installed apps rather than a hardcoded list.

```json
{"action": "open_app", "app": "Microsoft Word"}
```

The `--generate` output must look like this:

```json
{
  "actor": "## My Skill\nActor documentation here..."
}
```

### Installing a Skill

Drop the skill folder into `/skills`. The orchestrator scans the directory on startup and picks it up automatically.

```
skills/
  my-skill/
    skill.json
    actor_skill.md
    skill.py
```

### Creating a Skill

Skills live in `/skills/<skill-name>/`. The minimum requirement is a `skill.json`. Everything else depends on what type of skill you're building.

Documentation-only:
```
skills/my-app-guide/
  skill.json
  actor_skill.md
```

Static skill with actions:
```
skills/my-tool/
  skill.json
  actor_skill.md
  skill.py
```

Dynamic skill:
```
skills/my-dynamic-tool/
  skill.json
  skill.py      <- must handle --generate
```

When an action is invoked, the orchestrator calls the entry point as a subprocess with all action arguments (minus the `"action"` key itself) passed as a JSON string in `sys.argv[1]`:

```python
import sys, json

if __name__ == "__main__":
    args = json.loads(sys.argv[1])
    do_something(args.get("my_param"))
```

### skill.json Schema

```json
{
  "name": "my-skill",
  "description": "Short description shown to the skill installation model when deciding what to load",
  "actions": ["action_name"],
  "entry": "skill.py",
  "enabled": true,
  "dynamic_context": false,
  "generated_for_actor": true
}
```

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Identifier. Should match the folder name. |
| `description` | Yes | Shown to the skill installation model. Write this clearly, because it's how the model decides whether to load this skill for a given task. Vague descriptions get missed. |
| `actions` | Yes | List of action names this skill registers. Use `[""]` for documentation-only skills. |
| `entry` | No | Entry point filename. Omit for documentation-only skills. |
| `enabled` | No | Set to `false` to disable without deleting. Defaults to `true`. |
| `dynamic_context` | No | Set to `true` to enable runtime context generation. Entry point must handle `--generate` argument. |
| `generated_for_actor` | No | Used with `dynamic_context: true`. Tells the orchestrator this skill produces actor documentation. |

---

## Architecture

Here's what happens when you give Kodo a task.

### Skill Installation Phase

Before execution starts, `SkillInstallationMode` makes a call to a model with the task description and a compact summary of all available skills. The model returns a list of skill names it thinks are relevant. Those skills get loaded and their documentation is read or generated, held ready to inject into the actor's prompt.

The model first sees the name and the description from `skills.json` and picks what it needs, and the full documentation is only loaded if the skill is selected. This keeps the main system prompt from bloating with content that has nothing to do with the current task.

### Autonomy Mode

```
Task
  -> SkillInstallationMode
  -> AutonomyOrchestrator
  -> ActorModel (per turn) (reads UI tree, emits one action, updates history)
  -> Action Parser
    -> Interaction Layer
```

The actor runs in a free loop without an upfront plan and a `history` string as its working memory across turns. Each turn the model reads the live UI state, reasons about what to do next, acts, and appends a one-line summary to the history.

The actor also signals state. `DONE` ends the run. `STUCK` and `RETRY` add the failure message as context and loop again. `REPLAN` allows the actor to override its own next step entirely, substituting a new one of its choosing mid-execution.

`DONE` is not taken at face value. Before accepting it, the orchestrator checks whether the element the actor claimed to have acted on is actually present in the active window. If it isn't, the actor gets pushed back with a message telling it what's missing. The Gemini incident above would have been caught by this if the element check had matched -- it didn't, because the task completion condition was ambiguous.

The actor can request skill installation mid-task via `{"action": "install_skills", "skills": [...]}`. This pauses execution, loads the requested skills, and injects them into the next turn's context.

### UI Context and the Accessibility Tree

`ContextProvider` reads the active window using pywinauto's UIA backend, walking every descendant element and filtering by control type, bounds, and content. Elements with no text, no name, and no value are discarded. Elements outside the window bounds are discarded. The result is a flat list of `ControlType | name='...' | x=... y=...` strings the actor reasons over.

`UITreeHandler` sits on top of this and sends differential updates. If the tree changes by less than 20% between reads, it sends only the added and removed elements. If it changes by 20% or more (a page navigation, a new dialog, a full app switch) it sends the whole tree. This keeps the context window from filling with redundant state on every turn.

### Python Code Execution

The `python` action lets the actor write and run arbitrary Python code in-task. `PythonRunner` handles it by parsing the code's imports using Python's AST module, auto-installing any missing third-party packages into a dedicated `.kodo_venv` virtual environment, and running the code in a subprocess with a configurable timeout.

The stdout, stderr, and a result type (`SUCCESS`, `ERROR`, `TIMEOUT`, `PY_EXCEPTION`) come back to the orchestrator as context for the next action. The actor can use this to write files, launch applications, manipulate the clipboard, or query system state without touching the UI at all.

### A Few Other Things Worth Knowing

The context provider attempts to auto-expand ComboBox elements while reading the tree. If a dropdown is collapsed, it calls the UIA expand interface on it before extracting its contents. This means the actor can see dropdown options without having to click them open first.

There's a `strip_markdown_json` utility that strips markdown code fences from model responses before parsing. Models occasionally wrap their JSON output in backticks regardless of what the system prompt says, so it runs on every response as a precaution.
