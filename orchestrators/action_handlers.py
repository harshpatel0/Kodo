from utils.logger import logger
import json
from mcp.types import CallToolResult, TextContent
from settings.settings import settings

from orchestrators.parse_action import parse_action

MAX_REPLAN_LOOP = settings.orchestrator.max_replan_loop

from result_types import PrimitiveActionResult, ActionResult, DirectiveActionResult
from interactions.direct_app_control.types import *

from interactions.skills.types import KodoSkillResult

_consecutive_tool_errors: dict[str, int] = {}
MAX_CONSECUTIVE_TOOL_ERRORS = 3


def _format_output_block(stdout: str, stderr: str) -> str:
    """Only include sections that actually have content — skip the boilerplate
    "no output"/"no errors" filler that used to print on every single call."""
    parts = []
    if stdout.strip():
        parts.append(f"\n## Output\n{stdout}")
    if stderr.strip():
        parts.append(f"\n## Errors\n{stderr}")
    return "".join(parts)


def handle_proceed(step_count: int, iterations: int, in_autonomy: bool) -> ActionResult:
    if not in_autonomy:
        return ActionResult(
            signal="BREAK",
            step_count=step_count + 1,
            iterations=0,
            replan_history=[],
            additional_context="",
        )
    return ActionResult(
        signal="CONTINUE",
        iterations=iterations + 1,
        replan_history=[],
        additional_context="",
    )


def handle_done() -> ActionResult:
    logger.info("The actor model claims the task is done, hard exiting...")
    from utils import toaster

    toaster.update(title="Task Completed", message="Kodo claims the task is complete")
    return ActionResult(signal="BREAK", hard_exit=True)


def handle_stuck(action: dict, iterations: int, in_autonomy: bool) -> ActionResult:
    logger.info(
        "The Actor Model claims it is stuck, running another iteration with added context"
    )

    last_action = action.get("action", "")
    last_args = {k: v for k, v in action.items() if k != "action"}
    new_context = (
        f"[STUCK] Last action: {last_action} {json.dumps(last_args)}\n"
        f"{action.get('message', '')}"
    )
    return ActionResult(
        signal="CONTINUE",
        additional_context=new_context,
        iterations=iterations + 1,
    )


def handle_replan(
    next_action: str, replan_history: list[str], additional_context: str
) -> ActionResult:
    updated_history = replan_history + [next_action]

    normalized = [a.strip().lower() for a in updated_history]
    tail = (
        normalized[-MAX_REPLAN_LOOP:]
        if len(normalized) >= MAX_REPLAN_LOOP
        else normalized
    )

    hard_exit = None
    if len(tail) == MAX_REPLAN_LOOP and len(set(tail)) == 1:
        logger.critical(
            f"Replan loop detected ({MAX_REPLAN_LOOP} identical replans), forcing exit."
        )
        hard_exit = True

    logger.info("[ACTION_HANDLER] Replan requested, overriding instruction.")

    new_context = (
        additional_context
        + "\n[REPLAN] The task below is a sub-step inserted by replan. Complete it and "
        "act — do not emit `done` for the overall task from this step."
    )
    return ActionResult(
        signal="CONTINUE",
        additional_context=new_context,
        temp_task=next_action,
        replan_history=updated_history,
        hard_exit=hard_exit,
    )


def handle_retry(
    additional_context: str, error_message: str, action: dict, iterations: int
) -> ActionResult:
    logger.warning(f"[ACTION_HANDLER] Retrying with added context (iteration {iterations})")
    user_message = action.get("message", "")
    parts = []
    if user_message:
        parts.append(f"[NOTE] {user_message}")
    if error_message:
        parts.append(f"[ERROR] {error_message}")
    else:
        parts.append(
            "[ERROR] Could not parse your action. Output exactly one JSON "
            "object (or array) per response with a valid action name and arguments."
        )
    new_context = "\n".join(parts)
    return ActionResult(signal="CONTINUE", additional_context=new_context)


def handle_skill_invocations(
    action_result: KodoSkillResult,
    additional_context: str,
    in_autonomy: bool,
    step_count: int,
) -> ActionResult:
    logger.debug(action_result)
    action_result_type = action_result.result
    action_result_stderr = action_result.skill_errors or ""
    action_result_stdout = action_result.skill_output or ""

    logger.debug(
        f"Action Result Type for Custom Actions: {action_result_type}\nAction Result stderr: {action_result_stderr}\nAction Result stdout: {action_result_stdout}"
    )

    if action_result_type == "IMPORT_DISCOVERY_ERROR":
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"[ERROR] Could not discover imports in the code/skill:\n{action_result_stderr}\n"
            f"Hint: prefer an installed skill over inline Python when one covers this.",
        )

    elif action_result_type == "PACKAGE_INSTALL_ERROR":
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"[ERROR] Package install failed, code/skill did not run:\n{action_result_stderr}",
        )

    elif action_result_type == "TIMEOUT":
        output_block = _format_output_block(action_result_stdout, action_result_stderr)
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"[ERROR] Killed after exceeding the timeout.{output_block}",
        )

    elif action_result_type == "PY_EXCEPTION":
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"[ERROR] Exception while running:\n{action_result_stderr}",
        )

    elif action_result_type == "ERROR":
        output_block = _format_output_block(action_result_stdout, action_result_stderr)
        return ActionResult(
            signal="CONTINUE",
            additional_context=additional_context
            + f"[ERROR] Skill reported a severe error.{output_block}",
        )

    elif action_result_type == "SUCCESS":
        output_block = _format_output_block(action_result_stdout, action_result_stderr)
        if not output_block:
            output_block = "\n(no output)"
        return ActionResult(
            signal="BREAK",
            step_count=step_count + 1 if not in_autonomy else None,
            replan_history=[],
            additional_context=additional_context + f"# Skill Result{output_block}",
        )

    else:
        logger.error(
            f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type."
        )
        raise Exception(
            f"Unhandled action result: '{action_result}'. The LLM may have hallucinated an action type."
        )


def handle_mcp_tool_call_result(action_result: CallToolResult) -> ActionResult:
    logger.debug(msg=action_result)

    text_output = "\n".join(
        block.text for block in action_result.content if isinstance(block, TextContent)
    )
    tag = "[ERROR] " if action_result.isError else ""
    new_context = f"# MCP Tool Call Result\n{tag}{text_output}"
    return ActionResult(signal="CONTINUE", additional_context=new_context)


def handle_directive_result(directive: str) -> ActionResult:
    return ActionResult(signal="CONTINUE", directive=directive)


def call_action(
    action: dict,
    step_count: int = 0,
    iterations: int = 0,
    in_autonomy: bool = False,
    additional_context: str = "",
    replan_history: list[str] | None = None,
) -> ActionResult:
    """Parse the action and route to the appropriate handler. Pure function — returns ActionResult without side effects."""
    if replan_history is None:
        replan_history = []

    parsed_action = parse_action(action=action)

    if isinstance(parsed_action, PrimitiveActionResult):
        command = parsed_action.command
        if command == "PROCEED":
            action_result = handle_proceed(step_count, iterations, in_autonomy)
        elif command == "DONE":
            action_result = handle_done()
        elif command == "STUCK":
            action_result = handle_stuck(action, iterations, in_autonomy)
        elif command == "REPLAN":
            next_action = action.get("next", "")
            action_result = handle_replan(
                next_action, replan_history, additional_context
            )
        elif command == "RETRY":
            action_result = handle_retry(
                additional_context, parsed_action.error_message, action, iterations
            )
        else:
            raise NotImplementedError(f"Unexpected primitive command: {command}")

    elif isinstance(parsed_action, KodoSkillResult):
        action_result = handle_skill_invocations(
            parsed_action, additional_context, in_autonomy, step_count
        )

    elif isinstance(parsed_action, CallToolResult):
        tool_name = action.get("tool", action.get("action", ""))
        if parsed_action.isError:
            _consecutive_tool_errors[tool_name] = (
                _consecutive_tool_errors.get(tool_name, 0) + 1
            )
        else:
            _consecutive_tool_errors[tool_name] = 0

        consecutive = _consecutive_tool_errors.get(tool_name, 0)
        if consecutive >= MAX_CONSECUTIVE_TOOL_ERRORS:
            _consecutive_tool_errors[tool_name] = 0
            action_result = ActionResult(
                signal="CONTINUE",
                additional_context=(
                    f"[ERROR] '{tool_name}' has failed {consecutive} times in a row the "
                    f"same way. Stop using it this way — choose a different approach."
                ),
            )
        else:
            action_result = handle_mcp_tool_call_result(parsed_action)

    elif isinstance(parsed_action, DirectAppConnectionResult):
        tag = "" if parsed_action.success else "[ERROR] "
        context = f"# Connect Result\n{tag}{parsed_action.message}"
        if parsed_action.controls_text:
            context += f"\n\n## Controls\n{parsed_action.controls_text}"

        action_result = ActionResult(
            signal="CONTINUE",
            additional_context=context,
        )

    elif isinstance(parsed_action, DirectAppProcessList):
        action_result = ActionResult(
            signal="CONTINUE",
            additional_context=f"# Processes\n{str(parsed_action)}",
        )

    elif isinstance(parsed_action, DirectAppControlListResult):
        if parsed_action.error:
            context = f"# Controls\n[ERROR] {parsed_action.error}"
        elif parsed_action.controls:
            context = f"# Controls\n{str(parsed_action)}"
        else:
            context = "# Controls\n(none — no interactive controls exposed for this window)"
        action_result = ActionResult(
            signal="CONTINUE",
            additional_context=context,
        )

    elif isinstance(parsed_action, DirectAppInteractionResult):
        tag = "" if parsed_action.success else "[ERROR] "
        action_result = ActionResult(
            signal="CONTINUE",
            additional_context=f"# Interaction Result\n{tag}{parsed_action.message}",
        )

    elif isinstance(parsed_action, DirectiveActionResult):
        action_result = handle_directive_result(parsed_action.directive)

    else:
        logger.warning("Unexpected result path in call_action")
        raise NotImplementedError(f"Unexpected result type: {type(parsed_action)}")

    action_result.raw_result = parsed_action
    return action_result
