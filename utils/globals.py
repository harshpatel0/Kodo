from settings.settings import settings

PYTHON_RUNNER_VENV_NAME = ".kodo_venv"

API_BIND_TO_ALL_IPS = True
API_PORT = 5636
WEB_PORT = 5173

API_DESKTOP_STREAMING_FRAME_RATE = (
    30
    if not settings.web_ui.desktop_streaming_frame_rate
    else settings.web_ui.desktop_streaming_frame_rate
)
API_DESKTOP_STREAMING_PICTURE_QUALITY = (
    85
    if not settings.web_ui.desktop_streaming_quality_percentage
    else settings.web_ui.desktop_streaming_quality_percentage
)

ACTOR_MODEL_ENABLE_DEBUG_OUTPUT_PROMPTS_AND_RESULT_TO_FILE = False
ACTOR_MODEL_DEBUG_USER_PROMPT_CONSTRUCTION_TO_FILE = "dbg_actor_model.txt"

MODEL_DEFINITIONS_ENABLE_DEBUG_OLLAMA_REQUESTS = False
MODEL_DEFINITIONS_DEBUG_OLLAMA_REQUESTS_TO_FILE = "dbg_make_ollama_request.txt"

# Threshold for switching from diff to full UI tree.
# When the proportion of changed elements exceeds this percentage the full tree is sent.
CONTEXT_PROVIDER_UI_DIFF_THRESHOLD_PERCENTAGE = 30

ALLOWED_CONTROL_TYPES = {
    # Core interactive controls
    "Button",
    "Edit",
    "ComboBox",
    "List",
    "ListItem",
    "Menu",
    "MenuItem",
    "MenuBar",
    "CheckBox",
    "RadioButton",
    "Slider",
    "Spinner",
    # Text + document
    "Text",
    "Document",
    # Containers / structure
    "Pane",
    "Group",
    "Window",
    "Custom",
    # Navigation / hierarchy
    "Tree",
    "TreeItem",
    "Tab",
    "TabItem",
    # Advanced / less common but useful
    "Hyperlink",
    "DataItem",
    "DataGrid",
    "Table",
    # Tooling / UX
    "ToolBar",
    "StatusBar",
    "TitleBar",
    # Modern UI patterns
    "SplitButton",
    "Thumb",
    "ProgressBar",
}

DAC_ACTIONS = frozenset(
    {
        "list_processes",
        "connect",
        "list_controls",
        "interact",
        "expand",
        "collapse",
        "set_value",
        "scroll",
        "set_range_value",
        "get_grid_item",
        "minimize_window",
        "maximize_window",
        "restore_window",
        "close_window",
    }
)

STRUCTURAL_TYPES = {"Pane", "Group", "Window", "Custom"}
import platform

IS_RUNNING_WINDOWS = platform.system() == "Windows"

AVAILABLE_INTERACTION_LAYERS: list[str] = [
    # Action Helpers - these define execution semantics (batching, daemons, watchdogs) rather than
    # app-specific tools, and are listed first so their rules get merged into the prompt right after
    # the base prompt, ahead of the tool-reference layers below.
    "daemons",
    "multi_actions",
    "watchdog",
    "direct_app_control",
    "mcps",
    "pc_actions",
    "python",
    "skills",
]

RUNTIME_FILE_LOCATION = "temp"
CLAUDE_CODE_PROVIDER_SYSTEM_PROMPT_FILE_LOCATION = (
    f"{RUNTIME_FILE_LOCATION}/system_prompt"
)
