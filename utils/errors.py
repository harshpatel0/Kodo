from utils import check_layer
from utils.globals import DAC_ACTIONS

ACTION_LAYERS: dict[str, str] = {
    "mcp_tool_call": "mcps",
    "python": "python",
    "click": "pc_actions",
    "double_click": "pc_actions",
    "type": "pc_actions",
    "submit": "pc_actions",
    "press_key": "pc_actions",
    "press_hotkey": "pc_actions",
    "drag": "pc_actions",
    "scroll_v": "pc_actions",
    "scroll_h": "pc_actions",
    "clear_field": "pc_actions",
    "create_daemon": "daemons",
    "unregister_daemon": "daemons",
    "watchdog": "watchdog",
}
# Derive DAC entries from the single source of truth
ACTION_LAYERS.update({action: "direct_app_control" for action in DAC_ACTIONS})

_ALWAYS_VALID_ACTIONS = ["done", "stuck", "retry", "replan", "directive"]


def unknown_action_error(attempted: str) -> str:
    layer = ACTION_LAYERS.get(attempted)
    if layer and not check_layer(layer):
        return (
            f"The action '{attempted}' requires the '{layer}' interaction layer, "
            f"which is currently disabled by the user"
        )
    # Filtered at call time, not import time: an unrecognized action name must
    # only be offered actions from layers actually enabled this session.
    enabled_actions = sorted(
        action for action, action_layer in ACTION_LAYERS.items()
        if check_layer(action_layer)
    ) + _ALWAYS_VALID_ACTIONS
    return (
        f"The action '{attempted}' does not exist. "
        f"Valid actions are: {', '.join(enabled_actions)}."
    )
