import json
import os
import shutil
import subprocess
import threading
import time

from .base import ModelProvider, ChatMessage, ChatResponse
from utils.logger import logger
from settings.settings import settings

from utils import toaster

_ARGV_BUDGET_CHARS = 4_000

_TRANSIENT_ERRORS = (
    "overloaded",
    "rate limit",
    "rate_limit",
    "429",
    "500",
    "502",
    "503",
    "internal server error",
    "econnreset",
    "etimedout",
    "socket hang up",
    "fetch failed",
)

_UNKNOWN_FLAG_MARKERS = (
    "unknown option",
    "unknown argument",
    "unrecognized option",
    "unknown flag",
)

_running_processes: set[subprocess.Popen] = set()
_running_processes_lock = threading.Lock()

_written_prompts: dict[str, str] = {}
_written_prompts_lock = threading.Lock()


def _is_transient(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in _TRANSIENT_ERRORS)


def _unknown_flag(text: str) -> bool:
    lowered = (text or "").lower()
    return any(marker in lowered for marker in _UNKNOWN_FLAG_MARKERS)


def _try_pass_cli_json(text: str) -> str:
    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1] if "\n" in cleaned else ""
        if "```" in cleaned:
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

    if cleaned.startswith(("{", "[")):
        return cleaned

    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        end = cleaned.rfind(closer)
        if start != -1 and end > start:
            return cleaned[start : end + 1].strip()

    return cleaned


class _TransientCliError(RuntimeError):
    """CLI failure worth retrying (overload, rate limit, network, timeout)."""


class _UnsupportedFlagError(RuntimeError):
    """Installed CLI version rejected one of the optional flags."""

    def __init__(self, flag: str, detail: str):
        super().__init__(f"claude CLI does not support {flag}: {detail}")
        self.flag = flag


class ClaudeCodeProvider(ModelProvider):
    use_caching = False

    @staticmethod
    def kill_all_running() -> None:
        """Wired to the stop control. Safe to call from any thread."""
        with _running_processes_lock:
            processes = list(_running_processes)
        for process in processes:
            try:
                process.kill()
            except Exception:
                pass

    def __init__(
        self,
        cli_path: str = "claude",
        system_prompt_path: str = "system_prompt",
        timeout: int = 300,
        effort: str = "low",
        model: str = "sonnet",
        fallback_model: str = "",
        max_retries: int = 3,
        retry_delay_seconds: int = 5,
        context_warning_tokens: int = 150_000,
        use_caching: bool = False,
        **unused,
    ):
        resolved = shutil.which(cli_path)
        if not resolved:
            raise ValueError(
                f"Claude Code CLI ('{cli_path}') not found on PATH. Install it, run "
                f"`claude` once interactively to log in, or set "
                f"model_providers.claude_cli.cli_path to its full path."
            )

        self._argv_prefix = [resolved]
        if os.name == "nt" and resolved.lower().endswith((".cmd", ".bat")):
            self._argv_prefix = [os.environ.get("COMSPEC", "cmd.exe"), "/c", resolved]

        self.cli_path = resolved

        self.system_prompt_path = os.path.abspath(system_prompt_path)
        self.timeout = timeout

        self.effort = effort
        self.default_model = model
        self.fallback_model = fallback_model

        self.max_retries = max(1, int(max_retries))

        self.retry_delay_seconds = max(0, int(retry_delay_seconds))
        self.context_warning_tokens = int(context_warning_tokens)

        self._disabled_flags: set[str] = set()

        if use_caching:
            logger.warning(
                "[ClaudeCliProvider] use_caching is not supported and stays off; "
                "CLI sessions are not persisted between calls."
            )

        if unused:
            logger.debug(
                f"[ClaudeCliProvider] ignoring unknown settings: {sorted(unused)}"
            )

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:

        timer_start = time.monotonic()
        model = model or self.default_model

        system_text, turns, dropped_images = self._split_messages(messages)

        if not turns:
            raise ValueError("ClaudeCliProvider: no user/assistant messages provided.")

        if dropped_images:
            logger.warning(
                f"[ClaudeCliProvider] dropped {dropped_images} image attachment(s); "
                f"the CLI cannot read images with tools disabled."
            )

        system_path = (
            self._sync_system_prompt_to_file(system_text) if system_text else None
        )
        prompt = self._build_prompt(turns)
        self._warn_if_oversized(system_text, prompt)

        payload = self._run_with_retries(model, system_path, prompt)

        content = (payload.get("result") or "").strip()
        content = _try_pass_cli_json(content)

        if kwargs.get("thinking", False):
            logger.debug(
                "[ClaudeCliProvider] thinking was requested; the CLI does not return "
                "reasoning text in print mode, so ChatResponse.thinking stays None."
            )

        usage = payload.get("usage") or {}
        cache_read = int(usage.get("cache_read_input_tokens") or 0)

        global_caching = getattr(settings, "caching", None)
        if global_caching and getattr(global_caching, "log_stats", False):
            logger.info(f"Cache Control: {cache_read}")

        return ChatResponse(
            content=content,
            thinking=None,
            input_tokens=int(usage.get("input_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or 0),
            total_duration_ms=int((time.monotonic() - timer_start) * 1000),
            cache_read_tokens=cache_read,
            cache_write_tokens=int(usage.get("cache_creation_input_tokens") or 0),
        )

    # Prompt Claude CLI

    def _sync_system_prompt_to_file(self, system_text: str) -> str:
        path = self.system_prompt_path

        with _written_prompts_lock:
            if _written_prompts.get(path) == system_text and os.path.isfile(path):
                return path

            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)

            with open(path, "w", encoding="utf-8") as handle:
                handle.write(system_text)

            _written_prompts[path] = system_text

        logger.debug(
            f"[ClaudeCliProvider] system prompt written to {path} "
            f"({len(system_text)} chars)"
        )
        return path

    @staticmethod
    def _split_messages(messages: list[ChatMessage]) -> tuple[str, list[str], int]:
        system_chunks: list[str] = []
        turns: list[str] = []
        dropped_images = 0

        for msg in messages:
            if msg.role == "system":
                if msg.content:
                    system_chunks.append(msg.content)
                continue

            if getattr(msg, "images", None):
                dropped_images += len(msg.images)

            label = "Assistant" if msg.role == "assistant" else "User"
            turns.append(f"[{label}]\n{msg.content or ''}")

        return "\n\n".join(system_chunks), turns, dropped_images

    @staticmethod
    def _build_prompt(turns: list[str]) -> str:
        # Single turn is the common case, so send it plain: nothing sits between
        # the system prompt and the task.
        if len(turns) == 1:
            body = turns[0].split("\n", 1)[-1]
        else:
            body = "\n\n".join(turns)

        body += (
            "\n\nRespond with exactly one JSON object and nothing else: "
            "no prose before or after it, no markdown code fences."
        )
        return body

    def _warn_if_oversized(self, system_text: str, prompt: str) -> None:
        estimated = (len(system_text) + len(prompt)) // 4
        if estimated > self.context_warning_tokens:
            logger.warning(
                f"[ClaudeCliProvider] request is roughly {estimated} tokens, above the "
                f"{self.context_warning_tokens} warning threshold; the model may reject "
                f"it on context length."
            )
        else:
            logger.debug(f"[ClaudeCliProvider] request ~{estimated} tokens")

    # Claude Code call

    def _command(self, model: str, system_path: str | None) -> list[str]:
        command = self._argv_prefix + [
            "-p",
            "--output-format",
            "json",
            "--tools",
            "",
            "--model",
            model,
        ]

        if system_path:
            command += ["--system-prompt-file", system_path]

        for flag, args in self._optional_flags().items():
            if flag not in self._disabled_flags:
                command += args

        argv_chars = sum(len(part) for part in command)

        if argv_chars > _ARGV_BUDGET_CHARS:
            raise RuntimeError(
                f"ClaudeCliProvider command line is {argv_chars} chars, over the "
                f"{_ARGV_BUDGET_CHARS} budget."
            )

        return command

    def _optional_flags(self) -> dict[str, list[str]]:
        flags = {
            "--no-session-persistence": ["--no-session-persistence"],
            "--permission-prompts": ["--permission-prompts", "none"],
            "--effort": ["--effort", self.effort],
        }
        if settings.model_providers.claude_code.fallback_model:
            flags["--fallback-model"] = ["--fallback-model", self.fallback_model]

        if settings.model_providers.claude_code.run_bare:
            flags["--bare"] = ["--bare"]

        return flags

    def _build_env(self) -> dict[str, str]:
        """Bare mode reads auth strictly from ANTHROPIC_API_KEY, so this gets it."""
        env = os.environ.copy()

        if not settings.model_providers.claude_code.run_bare:
            return env

        key_env_var = settings.model_providers.claude_code.claude_code_api_key_env_var
        api_key = os.environ.get(key_env_var) if key_env_var else None

        if api_key:
            env["ANTHROPIC_API_KEY"] = api_key
        else:
            logger.warning(
                f"[ClaudeCliProvider] run_bare is on but {key_env_var!r} is unset; "
                f"the CLI will fail to authenticate."
            )

        return env

    def _run_with_retries(
        self, model: str, system_path: str | None, prompt: str
    ) -> dict:
        last_error: Exception | None = None
        attempt = 0

        while attempt < self.max_retries:
            try:
                return self._run_once(model, system_path, prompt)
            except _UnsupportedFlagError as e:
                # Does not consume an attempt: the call never reached the model,
                # and the flag set is finite so this cannot spin.
                self._disabled_flags.add(e.flag)
                logger.warning(
                    f"[ClaudeCliProvider] {e.flag} rejected by the installed CLI; "
                    f"disabling it for this session and retrying."
                )
                continue
            except _TransientCliError as e:
                attempt += 1
                last_error = e
                if attempt >= self.max_retries:
                    break
                delay = self.retry_delay_seconds * (2 ** (attempt - 1))
                toaster.update(
                    "Model currently unavailable",
                    "Claude Code is busy or unreachable; retrying the next action.",
                )
                logger.warning(
                    f"[ClaudeCliProvider] transient failure ({e}). Waiting {delay}s "
                    f"before retry (attempt {attempt}/{self.max_retries})..."
                )
                time.sleep(delay)

            except Exception as e:
                logger.error(f"[ClaudeCliProvider] CLI call failed: {e}")
                toaster.update(
                    "Model currently unavailable",
                    "The Claude Code CLI returned an error.",
                )
                raise

        toaster.update(
            "Model currently unavailable",
            f"Claude Code failed after {self.max_retries} attempts.",
        )
        raise last_error or RuntimeError(
            f"claude CLI request failed after {self.max_retries} retries"
        )

    def _run_once(self, model: str, system_path: str | None, prompt: str) -> dict:
        process = subprocess.Popen(
            self._command(model, system_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=self._build_env(),
        )
        with _running_processes_lock:
            _running_processes.add(process)

        try:
            stdout, stderr = process.communicate(input=prompt, timeout=self.timeout)
        except subprocess.TimeoutExpired as e:
            process.kill()
            process.communicate()
            raise _TransientCliError(
                f"claude CLI timed out after {self.timeout}s"
            ) from e
        finally:
            with _running_processes_lock:
                _running_processes.discard(process)

        if process.returncode != 0:
            detail = self._extract_error_detail(stderr, stdout)
            self._raise_for_detail(detail, f"exited with code {process.returncode}")

        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"claude CLI returned non-JSON output: {(stdout or '').strip()[:500]}"
            ) from e

        if payload.get("is_error"):
            detail = str(payload.get("result") or payload.get("subtype") or "").strip()
            self._raise_for_detail(detail[:500], "reported an error")

        return payload

    @staticmethod
    def _extract_error_detail(stderr: str, stdout: str) -> str:
        """Pull the human-readable message out of a failed run.

        On a non-zero exit the CLI still prints its usual JSON envelope to
        stdout, with the actual error in `result`/`subtype` — fields that sort
        after `usage`, so blindly truncating the raw text cuts them off before
        they're ever seen. Parse first, truncate second.
        """
        stderr = (stderr or "").strip()
        if stderr:
            return stderr[:500]

        stdout = (stdout or "").strip()
        try:
            payload = json.loads(stdout)
        except json.JSONDecodeError:
            return stdout[:500]

        detail = str(payload.get("result") or payload.get("subtype") or "").strip()
        return (detail or stdout)[:500]

    def _raise_for_detail(self, detail: str, context: str) -> None:
        if _unknown_flag(detail):
            for flag in self._optional_flags():
                if flag in detail and flag not in self._disabled_flags:
                    raise _UnsupportedFlagError(flag, detail)

        message = f"claude CLI {context}: {detail}"
        if _is_transient(detail):
            raise _TransientCliError(message)
        raise RuntimeError(message)
