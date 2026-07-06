from prompts.prompts import (
    construct_actor_mode_prompt,
    construct_autonomy_mode_prompt,
    construct_planner_mode_prompt,
    construct_skill_installation_mode_prompt,
)

PLANNER_SYSTEM_PROMPT = construct_planner_mode_prompt()
ACTOR_SYSTEM_PROMPT = construct_actor_mode_prompt()
AUTONOMY_MODE_SYSTEM_PROMPT = construct_autonomy_mode_prompt()
SKILL_INSTALLATION_PROMPT = construct_skill_installation_mode_prompt()
