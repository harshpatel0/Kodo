import rootutils

root = rootutils.setup_root(__file__, pythonpath=True)

import json
from models.model_definitions import PlannerModel, SkillInstallationMode
from interactions.skills.skill_orchestrator import skill_orchestrator
import utils.utils as utils
from utils.logger import logger
from utils.loading_text import get_loading_text

from settings.settings import settings

from server.log_stream import web_emitter
from utils.runtime_globals import CURRENT_MODE

planner_model = PlannerModel()
skill_installation = SkillInstallationMode()


def make_plan(task: str):
    CURRENT_MODE = "PLANNER"
    planner_skills, actor_skills = skill_installation.run(task)

    logger.debug(f"Planner skills loaded: {planner_skills is not None}")
    logger.debug(f"Actor skills loaded: {actor_skills is not None}")

    logger.info(get_loading_text())
    chat_response = planner_model.run(task=task, skills=planner_skills)
    response = chat_response.content

    tokens_in = chat_response.input_tokens
    tokens_out = chat_response.output_tokens
    cache_read = chat_response.cache_read_tokens
    cache_write = chat_response.cache_write_tokens
    elapsed_s = chat_response.total_duration_ms / 1000
    token_rate = round((tokens_in + tokens_out) / elapsed_s, 1) if elapsed_s > 0 else 0

    web_emitter.metrics(
        {
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "elapsed_ms": chat_response.total_duration_ms,
            "model": settings.models.planner.model_name,
            "provider": settings.models.planner.provider,
            "mode": "autonomy" if settings.orchestrator.use_autonomy_mode else "actor",
            "cache_read_tokens": cache_read,
            "cache_write_tokens": cache_write,
        }
    )

    cache_str = ""
    if cache_read:
        cache_str += f" | Cache read: {cache_read}"
    if cache_write:
        cache_str += f" | Cache write: {cache_write}"
    logger.info(
        f"Tokens Used: Input: {tokens_in} tokens, Output: {tokens_out} tokens."
        f" Took {round(elapsed_s)} seconds. Token rate: {token_rate} tok/s{cache_str}"
    )

    plan, parse_error = utils.try_parse_json(response)

    if plan is None:
        logger.error(f"Planner model returned unparseable JSON: {parse_error}")
        logger.error(f"Raw response: {response[:500]}")
        plan = {"task": task, "steps": [], "_parse_error": parse_error}

    plan.setdefault("_actor_skills", actor_skills)

    web_emitter.plan(plan)
    web_emitter.thinking(chat_response.thinking)

    return plan
