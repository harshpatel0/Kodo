import time
import models.actor_model as actor_model
from context_provider import ContextProvider
from orchestrators.action_handlers import call_action
from interactions.skills.skill_orchestrator import skill_orchestrator
from models.model_definitions import SkillInstallationMode
from utils import logger
from settings.settings import settings
from result_types import ActionResult
from mcp.types import CallToolResult, TextContent
from interactions.skills.types import KodoSkillResult

from utils import estimate_tokens

DAC_ACTIONS = {
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


def truncate_data_list(item: list[str], max_tokens=400) -> list[str]:
    if estimate_tokens("\n".join(item)) <= max_tokens:
        return item

    trimmed = []

    for entry in reversed(item):
        candidate = "\n".join([entry] + trimmed)
        if estimate_tokens(candidate) > max_tokens:
            break
        trimmed.insert(0, entry)
    return trimmed


class History:
    def __init__(self) -> None:
        self.history: list[str] = []

    def __str__(self) -> str:
        history_list = truncate_data_list(self.history)
        return "\n".join(history_list)

    def append(self, text: str) -> None:
        self.history.append(text)


class Directive:
    def __init__(self) -> None:
        self.directive: list[str] = []

    def __str__(self) -> str:
        directive_list = truncate_data_list(self.directive)
        return "\n".join(directive_list)

    def append(self, text: str) -> None:
        self.directive.append(text)


class AutonomyOrchestrator:
    def __init__(self, task):
        self.task = task
        self.iterations = 0
        self.additional_context = ""
        self.context_provider = ContextProvider()
        self.skill_installation_mode = SkillInstallationMode()
        self.skill_orchestrator = skill_orchestrator
        self.hard_exit = False
        self.skills = ""

        self.punishment_tally = ""
        self.history = History()
        self.directive = Directive()
        self.runtime_skills = None
        self.last_action = None

        self.installed_skills = []
        self.step_count = 0
        self.replan_history = []
        self.temp_task = None
        self.step_result: dict = {}

    def _make_deterministic_history(
        self, ar: ActionResult, step_result: dict
    ) -> str | None:
        action = step_result.get("action", "")
        if not action:
            return None

        is_tool = False
        is_dac_error = False

        if action == "mcp_tool_call":
            is_tool = True
        elif action == "python":
            is_tool = True
        elif action in DAC_ACTIONS:
            raw = ar.raw_result
            if raw is not None:
                error = getattr(raw, "error", None) or getattr(
                    raw, "error_message", None
                )
                success = getattr(raw, "success", None)
                if error or (success is not None and not success):
                    is_dac_error = True
        elif skill_orchestrator.can_handle(action):
            is_tool = True

        if not is_tool and not is_dac_error:
            return None

        intent = step_result.get("history", "")
        summary = self._summarize_raw_result(ar.raw_result)
        if not summary:
            return intent
        if len(intent) + len(summary) < 300:
            return f"{intent} | {summary}"
        return f"{intent} | {summary[:250]}..."

    def _summarize_raw_result(self, raw) -> str | None:
        if raw is None:
            return None

        if isinstance(raw, CallToolResult):
            texts = [
                b.text
                for b in raw.content
                if isinstance(b, TextContent) and b.text.strip()
            ]
            if not texts:
                return None
            combined = "; ".join(texts)
            error_tag = " [ERROR]" if raw.isError else ""
            if len(combined) <= 200:
                return f"{combined}{error_tag}"
            return f"{combined[:197]}{error_tag}..."

        if isinstance(raw, KodoSkillResult):
            parts = []
            if raw.skill_output:
                parts.append(raw.skill_output[:200])
            if raw.result in ("ERROR", "TIMEOUT") and raw.skill_errors:
                err = raw.skill_errors[:200]
                parts.append(f"error: {err}")
            return " | ".join(parts) if parts else None

        error = getattr(raw, "error", None) or getattr(raw, "error_message", None)
        if error:
            return f"error: {str(error)[:200]}"

        message = getattr(raw, "message", None)
        if message:
            return str(message)[:200]

        return None

    def _apply(self, ar: ActionResult) -> None:
        if ar.step_count is not None:
            self.step_count = ar.step_count
        if ar.iterations is not None:
            self.iterations = ar.iterations
        if ar.replan_history is not None:
            self.replan_history = ar.replan_history
        if ar.additional_context is not None:
            self.additional_context = ar.additional_context
        if ar.hard_exit is not None:
            self.hard_exit = ar.hard_exit
        if ar.temp_task is not None:
            self.temp_task = ar.temp_task
        if ar.directive:
            self.directive.append(ar.directive)

    def _cleanup(self) -> None:
        self.temp_task = None
        self.additional_context = ""

    def _handle_skill_installation(self, requested_skills: list) -> None:
        skills_not_installed = [
            s for s in requested_skills if s not in self.installed_skills
        ]
        skills_already_installed = [
            s for s in requested_skills if s not in skills_not_installed
        ]
        installable = [
            s for s in skills_not_installed if self.skill_orchestrator.has_skill(s)
        ]
        unresolvable = [s for s in requested_skills if s not in installable]

        if unresolvable:
            logger.warning(f"Requested skills not found: {unresolvable}")
            self.additional_context += f"\nThe following requested skills could not be found: {unresolvable}. Proceed without them."

        if skills_already_installed:
            logger.warning(
                f"Not installing: {skills_already_installed}, already installed"
            )
            self.additional_context += f"\n The following skills are already installed: {skills_already_installed}, here are all available actions for a refresher: {self.skill_orchestrator.list_actions()}"

        self.runtime_skills = self.skill_orchestrator.load_all_requested_skills(
            installable, "actor"
        )

    def run_skill_installation_mode(self):
        actor_skills, installed_skills = self.skill_installation_mode.run(self.task)

        self.skills = actor_skills
        if isinstance(installed_skills, (list, tuple, set)):
            self.installed_skills = list(installed_skills)
        elif installed_skills is None:
            self.installed_skills = []
        else:
            self.installed_skills = [installed_skills]

    def run(self):
        directive_section = (
            f"\n## Directive\n{self.directive}\n" if str(self.directive).strip() else ""
        )

        while not self.hard_exit:
            max_iter = settings.orchestrator.autonomy_orchestrator.max_total_iterations

            logger.info(f"""
Running iteration {self.iterations+1} out of {max_iter}

Task = {self.task}

Directives
{directive_section}

Additional Context:
{self.additional_context}

History (truncated):
{str(self.history)}
""")

            if max_iter > 0 and self.iterations >= max_iter:
                self.hard_exit = True

            last_action_info = ""
            if self.step_result.get("action"):
                last_action_info = (
                    f"[LAST ACTION] action='{self.step_result['action']}' "
                    f"args={{{', '.join(f'{k}={v!r}' for k, v in self.step_result.items() if k != 'action')}}}\n"
                )

            punishment_tally = None
            if max_iter > 0:
                punishment_tally = f"Iteration {self.iterations+1} out of maximum {max_iter}\n{last_action_info}"

            try:
                self.step_result = actor_model.do_step(
                    task=self.task,
                    additional_context=self.additional_context,
                    skills=self.skills,
                    runtime_skills=self.runtime_skills,
                    punishment_tally=punishment_tally,
                    history=str(self.history),
                    available_skill_actions=self.skill_orchestrator.list_actions(),
                    directive=str(self.directive),
                )
            except KeyboardInterrupt:
                exit(1)
            except Exception as e:
                logger.error(f"Autonomy step failed: {e}")
                self.step_result = {
                    "action": "retry",
                    "message": f"Step execution error: {e}",
                }

            self.iterations += 1

            if self.step_result.get("install_skills"):
                self._handle_skill_installation(self.step_result["skills"])
                self.history.append(self.step_result.get("history", "None"))

            else:
                ar = call_action(
                    action=self.step_result,
                    iterations=self.iterations,
                    in_autonomy=True,
                    additional_context=self.additional_context,
                )
                self._cleanup()
                self._apply(ar)
                time.sleep(settings.orchestrator.action_settle_time)

                # Append to history
                # Use actual tool result for deterministic tools, fall back to model's self-reported history for everything else
                deterministic = self._make_deterministic_history(ar, self.step_result)
                if deterministic:
                    self.history.append(deterministic)
                else:
                    model_provided_history = self.step_result.get("history", "None")
                    self.history.append(model_provided_history)

                if settings.orchestrator.autonomy_orchestrator.toast_notify_history:
                    from winotify import Notification

                    toast = Notification(
                        app_id="Kodo",
                        title="Kodo Step Result",
                        msg=deterministic or self.step_result.get("history", "None"),
                    )
                    toast.show()
