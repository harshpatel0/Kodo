import os

from .base import ModelProvider, ChatMessage, ChatResponse
from utils.logger import logger
import anthropic as _anthropic
from settings.settings import settings
from models.provider.utils.cache_control import CacheControl

from utils.runtime_globals import CURRENT_MODE

import time


def determine_caching(setting_state: bool):
    """Disable Caching if the mode is not ACTOR or AUTONOMY as cache invalidation penalties will apply
    if planner or skill_installation mode prompts are cached
    """
    if setting_state and CURRENT_MODE in ("ACTOR", "AUTONOMY"):
        return True
    return False


class AnthropicProvider(ModelProvider):
    """Provider for Anthropic's Claude models. Uses anthropic Python SDK.
    Reads API key from environment variable at init time.
    """

    def __init__(
        self,
        api_key_env_var: str = "ANTHROPIC_API_KEY",
        base_url: str | None = None,
        use_caching: bool = False,
    ):
        try:
            import anthropic as _anthropic
        except ImportError:
            raise ImportError(
                "Anthropic-SDK is not installed. Run: pip install anthropic"
            )

        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            raise ValueError(
                f"Anthropic API key not found in environment variable '{api_key_env_var}'. "
                f"Set it and restart."
            )
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = _anthropic.Anthropic(**kwargs)
        self.use_caching = determine_caching(use_caching)
        self.bank = CacheControl(system_prompt="")

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:

        timer_start = time.monotonic()

        system_prompt = None
        api_messages = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
                continue

            role = "assistant" if msg.role == "assistant" else "user"
            content = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})
            if msg.images:
                for img_b64 in msg.images:
                    content.append(
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": img_b64,
                            },
                        }
                    )
            api_messages.append({"role": role, "content": content})

        if self.use_caching and api_messages:
            last_content = api_messages[-1]["content"]
            if last_content:
                last_content[-1]["cache_control"] = {"type": "ephemeral"}

        call_kwargs = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }

        if system_prompt:
            if self.use_caching:
                call_kwargs["system"] = [
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ]
            else:
                call_kwargs["system"] = system_prompt
        if kwargs.get("thinking", False):
            call_kwargs["thinking"] = {"type": "adaptive"}
            call_kwargs["temperature"] = (
                1.0  # Enabling Thinking forces temperature to 1.0
            )
            call_kwargs["max_tokens"] = 16384
        try:
            anthropic_effort = settings.model_providers.anthropic.effort
            if anthropic_effort:
                call_kwargs["output_config"] = {"effort": anthropic_effort}
        except AttributeError:
            pass

        try:
            for msg in api_messages:
                for block in msg["content"]:
                    if block.get("type") == "text":
                        self.bank.append(block["text"])
            response = self._client.messages.create(**call_kwargs)
        except _anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            raise

        content = ""
        thinking = None
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "thinking":
                thinking = (thinking or "") + block.thinking

        elapsed_time = int((time.monotonic() - timer_start) * 1000)
        self.bank.append(content.strip())

        return ChatResponse(
            content=content.strip(),
            thinking=thinking,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_duration_ms=elapsed_time,
        )
