"""Provider that shells out to the Claude Code CLI (`claude -p ...`) instead of
calling an HTTP API directly. Whatever the CLI is already logged into on this
machine -- a Pro/Max subscription via OAuth, or an API key -- is what actually
gets billed; this provider itself never touches ANTHROPIC_API_KEY.

Known limitations, read before relying on this:
  - Tool access is disabled (`--tools ""`) and the system prompt is fully
    overridden (`--system-prompt`, not `--append-system-prompt`) so this behaves
    like a plain chat completion rather than a coding-agent session -- without
    the override, Claude Code's own default identity makes it suspicious of and
    liable to refuse "just emit this JSON" style instructions.
  - `temperature` and `max_tokens` are accepted (to match the ModelProvider
    interface) but have no effect -- the CLI doesn't expose sampling controls.
  - `thinking` text isn't returned, and this isn't fixable by switching output
    formats: `--output-format json` reports thinking *token counts* only, and
    `--output-format stream-json` (checked directly) does emit a `thinking`
    content block when reasoning actually happens, but its `thinking` field is
    an empty string -- just an opaque `signature` blob, no readable text. The
    CLI doesn't expose reasoning content in non-interactive mode at all right
    now, so ChatResponse.thinking is always None here.
  - Each call is a fresh, non-persisted CLI session (`--no-session-persistence`)
    -- conversation state is carried entirely by the `messages` list, same as
    every other provider, not by any Claude Code session.
  - `model` must be one of the CLI's aliases: "haiku", "sonnet", "opus", "fable"
    (or a full model name, e.g. "claude-sonnet-5") -- not an API model slug. A
    role's own model_name (e.g. models.autonomy_actor.model_name) is used if
    set; model_providers.claude_code.model (default "sonnet") is the fallback
    when it isn't.
  - `effort` (low, medium, high, xhigh, max) sets `--effort`; configured at the
    provider level (model_providers.claude_code.effort, default "low"), same
    place the regular Anthropic provider keeps its own effort setting, since
    the CLI has no per-call way to pass it through ModelProvider.chat()'s
    existing parameters.
  - Latency is a full CLI process spawn per turn, not a lightweight HTTP call --
    expect it to be slower than the other providers here.
"""

import json
import shutil
import subprocess
import time

from .base import ModelProvider, ChatMessage, ChatResponse
from utils.logger import logger


class ClaudeCodeProvider(ModelProvider):
    use_caching = False

    def __init__(
        self,
        cli_path: str = "claude",
        timeout: int = 120,
        effort: str = "low",
        model: str = "sonnet",
    ):
        if not shutil.which(cli_path):
            raise ValueError(
                f"Claude Code CLI ('{cli_path}') not found on PATH. Install it and make "
                f"sure you're logged in (`claude` once interactively), or set "
                f"model_providers.claude_code.cli_path to its full path."
            )
        self.cli_path = cli_path
        self.timeout = timeout
        self.effort = effort
        self.default_model = model

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

        system_prompt = None
        turn_parts = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = (
                    f"{system_prompt}\n\n{msg.content}"
                    if system_prompt
                    else msg.content
                )
                continue

            if msg.images:
                logger.warning(
                    "ClaudeCodeProvider: image attachments aren't supported and were dropped."
                )

            role_label = "Assistant" if msg.role == "assistant" else "User"
            turn_parts.append(f"[{role_label}]\n{msg.content}")

        prompt = "\n\n".join(turn_parts)

        command = [
            self.cli_path,
            "-p",
            prompt,
            "--output-format",
            "json",
            "--tools",
            "",
            "--no-session-persistence",
            "--permission-prompts",
            "none",
            "--model",
            model,
            "--effort",
            self.effort,
        ]
        if system_prompt:
            command += ["--system-prompt", system_prompt]

        try:
            process = subprocess.run(
                command, capture_output=True, text=True, timeout=self.timeout
            )
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"claude CLI timed out after {self.timeout}s") from e

        if process.returncode != 0:
            raise RuntimeError(
                f"claude CLI exited with code {process.returncode}: {process.stderr.strip()}"
            )

        try:
            payload = json.loads(process.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"claude CLI returned non-JSON output: {process.stdout[:500]}"
            ) from e

        if payload.get("is_error"):
            raise RuntimeError(f"claude CLI reported an error: {payload.get('result')}")

        usage = payload.get("usage", {})
        elapsed_time = int((time.monotonic() - timer_start) * 1000)

        return ChatResponse(
            content=(payload.get("result") or "").strip(),
            thinking=None,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            total_duration_ms=elapsed_time,
            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
            cache_write_tokens=usage.get("cache_creation_input_tokens", 0),
        )
