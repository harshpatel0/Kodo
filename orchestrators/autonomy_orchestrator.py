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
from interactions.direct_app_control.types import (
    DirectAppProcessList,
    DirectAppControlListResult,
    DirectAppConnectionResult,
    DirectAppInteractionResult,
)

from utils.runtime_globals import CURRENT_MODE

import orchestrators.autonomy_helpers

from utils import estimate_tokens
from utils.globals import DAC_ACTIONS


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
        self.history = orchestrators.autonomy_helpers.history_manager
        self.directive = orchestrators.autonomy_helpers.directive_manager
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
            is_tool = True
        elif skill_orchestrator.can_handle(action):
            is_tool = True

        if not is_tool:
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
            if raw.isError:
                if estimate_tokens(combined) > 60:
                    return f"[ERROR]{error_tag}"
            elif estimate_tokens(combined) > 30:
                return None
            if len(combined) <= 200:
                return f"{combined}{error_tag}"
            return f"{combined[:197]}{error_tag}..."

        if isinstance(raw, KodoSkillResult):
            parts = []
            has_error = raw.result in ("ERROR", "TIMEOUT")
            if raw.skill_output:
                if estimate_tokens(raw.skill_output) <= (60 if has_error else 30):
                    parts.append(raw.skill_output[:200])
            if has_error and raw.skill_errors:
                if estimate_tokens(raw.skill_errors) <= 60:
                    err = raw.skill_errors[:200]
                    parts.append(f"error: {err}")
                else:
                    parts.append("[ERROR]")
            return " | ".join(parts) if parts else None

        if isinstance(raw, DirectAppProcessList):
            count = len(raw.processes)
            return f"Found {count} processes"

        if isinstance(raw, DirectAppControlListResult):
            if raw.error:
                return f"controls error: {raw.error[:200]}"
            count = len(raw.controls)
            return f"Found {count} controls"

        if isinstance(raw, DirectAppConnectionResult):
            return f"{'Connected' if raw.success else 'Failed'}: {raw.message[:200]}"

        if isinstance(raw, DirectAppInteractionResult):
            return f"{'Success' if raw.success else 'Failed'}: {raw.message[:200]}"

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
        CURRENT_MODE = "SKILL_INSTALLATION"
        actor_skills, installed_skills = self.skill_installation_mode.run(self.task)

        self.skills = actor_skills
        if isinstance(installed_skills, (list, tuple, set)):
            self.installed_skills = list(installed_skills)
        elif installed_skills is None:
            self.installed_skills = []
        else:
            self.installed_skills = [installed_skills]

    def run(self):
        CURRENT_MODE = "AUTONOMY"
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
            if isinstance(self.step_result, dict) and self.step_result.get("action"):
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

            self.runtime_skills = None
            self.iterations += 1

            if isinstance(self.step_result, list):
                contexts = []
                history_parts = []
                directives = []
                last_ar = None
                for single_action in self.step_result:
                    if (
                        not isinstance(single_action, dict)
                        or "action" not in single_action
                    ):
                        continue
                    ar = call_action(
                        action=single_action,
                        iterations=self.iterations,
                        in_autonomy=True,
                        additional_context=self.additional_context,
                    )
                    last_ar = ar
                    if ar.additional_context:
                        contexts.append(ar.additional_context)
                    if ar.directive:
                        directives.append(ar.directive)
                    if single_action.get("action") not in (
                        "create_daemon",
                        "unregister_daemon",
                    ):
                        deterministic = self._make_deterministic_history(
                            ar, single_action
                        )
                        if deterministic:
                            history_parts.append(deterministic)
                        else:
                            history_parts.append(single_action.get("history", "None"))
                    time.sleep(settings.orchestrator.action_settle_time)
                    if ar.hard_exit:
                        self.hard_exit = True
                        break
                if not self.hard_exit:
                    self._cleanup()
                if last_ar:
                    self._apply(last_ar)
                if contexts:
                    self.additional_context = "\n".join(contexts)
                for d in directives:
                    self.directive.append(d)
                combined_history = " | ".join(history_parts) if history_parts else ""
                if history_parts:
                    self.history.append(combined_history)
                if (
                    settings.orchestrator.autonomy_orchestrator.toast_notify_history
                    and combined_history
                ):
                    from winotify import Notification

                    toast = Notification(
                        app_id="Kodo",
                        title="Kodo Step Result (Batch)",
                        msg=combined_history,
                    )
                    toast.show()

            elif self.step_result.get("install_skills"):
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
                if self.step_result.get("action") in (
                    "create_daemon",
                    "unregister_daemon",
                ):
                    pass
                else:
                    deterministic = self._make_deterministic_history(
                        ar, self.step_result
                    )
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
