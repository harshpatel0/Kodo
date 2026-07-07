from pathlib import Path

from settings.settings import settings
from utils import check_layer
from typing import Literal, Tuple

prompts_folder = Path(__file__).parent.parent / "prompts"
interactions_folder = Path(__file__).parent.parent / "interactions"

from utils.globals import AVAILABLE_INTERACTION_LAYERS


def load_prompt(file: str, folder: Path = prompts_folder) -> str:
    path = folder / file

    if not path.exists():
        raise FileNotFoundError(f"Prompt file: {file} not found")

    return path.read_text(encoding="utf-8")


def construct_mode_prompt(mode: str) -> str:
    try:
        base_prompt = load_prompt(file=f"{mode}.md", folder=prompts_folder)
    except FileNotFoundError:
        print(f"Missing base prompt for {mode}")
        exit(1)

    active_layers = [
        layer for layer in AVAILABLE_INTERACTION_LAYERS if check_layer(layer)
    ]

    layers_header = (
        f"\n# Available Interaction Layers\n"
        f"The following interaction layers are enabled this session: {', '.join(active_layers)}.\n"
    )

    interaction_layer_prompts = ""

    for interaction_layer in active_layers:
        prompt_folder = interactions_folder / interaction_layer

        try:
            loaded_prompt = load_prompt(f"{mode}.md", prompt_folder)
            interaction_layer_prompts += loaded_prompt + "\n"
        except FileNotFoundError:
            pass

    custom_instructions = load_prompt("custom_instructions.md", prompts_folder)

    return base_prompt + "\n" + custom_instructions + "\n" + layers_header + interaction_layer_prompts


def construct_autonomy_mode_prompt() -> str:
    return construct_mode_prompt("autonomy")


def construct_actor_mode_prompt() -> str:
    return construct_mode_prompt("actor")


def construct_planner_mode_prompt() -> str:
    return construct_mode_prompt("planner")


def construct_skill_installation_mode_prompt() -> str:
    return construct_mode_prompt("skill_installation")
