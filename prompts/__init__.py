from prompts.prompts import (
    construct_autonomy_mode_prompt,
    construct_skill_installation_mode_prompt,
)

AUTONOMY_MODE_SYSTEM_PROMPT = construct_autonomy_mode_prompt()
SKILL_INSTALLATION_PROMPT = construct_skill_installation_mode_prompt()
