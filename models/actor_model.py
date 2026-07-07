from models.model_definitions import ActorModel

import utils.utils as utils
from utils.logger import logger
from utils.globals import (
    ACTOR_MODEL_ENABLE_DEBUG_OUTPUT_PROMPTS_AND_RESULT_TO_FILE,
    ACTOR_MODEL_DEBUG_USER_PROMPT_CONSTRUCTION_TO_FILE,
)

from server.log_stream import web_emitter
from settings.settings import settings

from interactions.direct_app_control.direct_app_control_handler import (
    direct_app_handler,
)

from interactions.daemons.daemons import daemon_provider

actor_model = ActorModel()


def log_to_debug_file(user_prompt: str, action: dict):
    with open(
        ACTOR_MODEL_DEBUG_USER_PROMPT_CONSTRUCTION_TO_FILE, "a", encoding="utf-8"
    ) as file:
        file.write(f"""
User Prompt
{"=" * 20}
{user_prompt}

Result
{"=" * 20}
{action}

{"=" * 20}
""")


def do_step(
    task: str,
    history=None,
    additional_context: str | None = None,
    punishment_tally=None,
    skills=None,
    runtime_skills=None,
    available_skill_actions=None,
    directive=None,
):

    cfg = (
        settings.models.autonomy_actor
        if settings.orchestrator.use_autonomy_mode
        else settings.models.actor
    )
    model_provider = cfg.provider
    model_name = cfg.model_name

    actor_model.construct_system_prompt(skills=skills)

    user_prompt = actor_model.construct_user_prompt(
        task=task, instruction=None, expected_result=None
    )

    if additional_context:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt, additional_context
        )

    if punishment_tally:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt,
            additional_context=punishment_tally,
            accompanying_message="Here are the number of iterations you have made on this task",
        )

    if available_skill_actions:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt,
            additional_context=available_skill_actions,
            accompanying_message="The following are the available skill actions, skill actions run like any skill, you are advised on how to run them already",
        )

    if runtime_skills:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt,
            additional_context=runtime_skills,
            accompanying_message="The following skill(s) was/were just installed and is now available to you:",
        )

    if (
        settings.direct_app_control.always_populate_connected_app_controls
        and direct_app_handler.is_app_connected()
    ):
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt=user_prompt,
            additional_context=str(direct_app_handler.list_process_str()),
            accompanying_message=f"Here are the controls of the connected app {direct_app_handler.return_app_window()} with PID {direct_app_handler.return_connected_pid}",
        )

    if str(daemon_provider):
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt=user_prompt,
            additional_context=str(daemon_provider),
            accompanying_message="""# Continuous Watchers (Daemons)
This is the CURRENT STATE from your persistent watchers — injected every turn automatically.
You do NOT need to manually call these tools as mcp_tool_call actions — the daemon already watches them.
Use the state below directly instead of re-querying.""",
        )
        
    if history:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt,
            additional_context=history,
            accompanying_message="Here is a running history of everything you said you did:",
        )

    if directive:
        user_prompt = actor_model.return_prompt_with_additional_context(
            user_prompt=user_prompt,
            additional_context=directive,
            accompanying_message="Here are directives from previous models, follow them:",
        )


    chat_response = actor_model.run(user_prompt)
    response = chat_response.content

    tokens_in = chat_response.input_tokens
    tokens_out = chat_response.output_tokens
    elapsed_s = chat_response.total_duration_ms / 1000
    token_rate = round((tokens_in + tokens_out) / elapsed_s, 1) if elapsed_s > 0 else 0

    web_emitter.metrics(
        {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "elapsed_ms": chat_response.total_duration_ms,
            "model": model_name,
            "provider": model_provider,
            "mode": "autonomy" if settings.orchestrator.use_autonomy_mode else "actor",
        }
    )

    logger.info(f"[LLM RAW] {response}")

    raw = utils.strip_markdown_json(response).strip()

    action, parse_error = utils.try_parse_json(raw)

    if not action:
        logger.warning(
            f"[JSON PARSE] Failed: {parse_error}. Raw: {raw[:500]}"
        )
        action = {
            "action": "retry",
            "message": f"Model returned unparseable response. {parse_error}. Raw output:\n{raw[:500]}",
        }

    if ACTOR_MODEL_ENABLE_DEBUG_OUTPUT_PROMPTS_AND_RESULT_TO_FILE:
        log_to_debug_file(user_prompt=user_prompt, action=action)

    logger.debug(action)

    web_emitter.action(action)
    web_emitter.thinking(chat_response.thinking if chat_response.thinking else "")

    logger.info(
        f"Tokens Used: Input: {tokens_in} tokens, Output: {tokens_out} tokens. "
        f"Took {round(elapsed_s)} seconds. Token rate: {token_rate} tok/s"
    )

    logger.info(f"Thinking: \n\t{chat_response.thinking}")

    return action
