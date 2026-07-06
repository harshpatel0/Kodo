from utils.logger import logger

MAX_CONSECUTIVE_ERRORS = 3


class _DaemonEntry:
    def __init__(self, daemon_id: int, action: dict):
        self.id = daemon_id
        self.action = action
        self.consecutive_errors = 0


class Daemons:
    def __init__(self):
        self._entries: list[_DaemonEntry] = []
        self._next_id = 0
        self._removed: list[str] = []

    def register_daemon(self, action: dict) -> None:
        self._entries.append(_DaemonEntry(self._next_id, action))
        self._next_id += 1

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

    def unregister_daemon(self, index: int) -> None:
        if 0 <= index < len(self._entries):
            self._entries.pop(index)

    def __str__(self) -> str:
        if not self._entries and not self._removed:
            return ""

        daemon_text = (
            "# Daemon Context - Current State (no need to re-query these tools)\n"
        )
        still_alive: list[_DaemonEntry] = []

        for entry in self._entries:
            from orchestrators.parse_action import parse_action

            parsed = parse_action(action=entry.action)
            result_str = str(parsed)

            if self._has_error(parsed):
                entry.consecutive_errors += 1
                daemon_text += (
                    f"\n## Watcher {entry.id}: {entry.action}\n"
                    f"State: {result_str}\n"
                    f"(warning: watcher failed {entry.consecutive_errors} consecutive time(s))\n"
                )
                if entry.consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    note = (
                        f"Watcher {entry.id} ({entry.action}) "
                        f"— auto-removed after {entry.consecutive_errors} consecutive failures"
                    )
                    daemon_text += f"(auto-removed)\n"
                    self._removed.append(note)
                    logger.warning(f"Daemon auto-removed: {note}")
                    continue
            else:
                entry.consecutive_errors = 0
                daemon_text += (
                    f"\n## Watcher {entry.id}: {entry.action}\n"
                    f"State: {result_str}\n"
                )

            still_alive.append(entry)

        self._entries = still_alive

        for note in self._removed:
            daemon_text += f"\n[Stale watcher] {note}\n"
        self._removed.clear()

        return daemon_text


daemon_provider = Daemons()
