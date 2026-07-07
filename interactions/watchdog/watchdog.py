import time
import hashlib
from dataclasses import dataclass
from typing import Any

from orchestrators.parse_action import parse_action


@dataclass
class WatchdogAction:
    action_result: Any
    hash: Any
    changed: bool


class Watchdog:
    """Watchdogs allow Kodo to send a read action and wait for a change in the response,
    e.g., from an MCP or the context of a hooked process"""

    def _has_error(self, parsed_action) -> bool:
        from mcp.types import CallToolResult
        from interactions.skills.types import KodoSkillResult

        if isinstance(parsed_action, CallToolResult) and parsed_action.isError:
            return True
        if isinstance(parsed_action, KodoSkillResult) and parsed_action.result in (
            "ERROR",
            "TIMEOUT",
        ):
            return True
        if hasattr(parsed_action, "error_message") and parsed_action.error_message:
            return True
        return False

    def _store_initial_action_result(self, action: dict) -> Any | None:
        action_result = parse_action(action=action)
        result_str = str(action_result)

        if self._has_error(action_result):
            return action_result

        self.hashed_result = hashlib.sha256(result_str.encode("utf-8")).hexdigest()
        return None

    def _run_action(self, action: dict) -> WatchdogAction:
        action_result = parse_action(action=action)
        result_str = str(action_result)

        action_hash = hashlib.sha256(result_str.encode("utf-8")).hexdigest()

        changed = True if action_hash != self.hashed_result else False

        return WatchdogAction(
            action_result=action_result, hash=action_hash, changed=changed
        )

    def start_watchdog(
        self, action: dict, timeout_seconds: int = 15, poll_duration=0.75
    ) -> Any:

        initial_store_result = self._store_initial_action_result(action=action)
        if initial_store_result is not None:
            return initial_store_result

        start_time = time.monotonic()

        while True:
            watchdog_result = self._run_action(action=action)

            if watchdog_result.changed:
                return watchdog_result

            if time.monotonic() - start_time >= timeout_seconds:
                # Receiving a Watchdog Result with a false `changed` means we can safely assume the result never changed within the timeout seconds
                return watchdog_result

            time.sleep(poll_duration)


# To use the Watchdog Manager, use watchdog_manager.start_watchdog(action) to start
watchdog_provider = Watchdog()
