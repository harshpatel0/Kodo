import os
import time

from openai import OpenAI

from .base import ModelProvider, ChatMessage, ChatResponse
from utils.logger import logger
from utils.runtime_globals import CURRENT_MODE


class OpenAICompatibleProvider(ModelProvider):
    """Provider for any OpenAI-compatible chat completions endpoint.

    Works with OpenRouter, Together AI, Groq, Azure OpenAI,
    and any other provider that exposes the standard OpenAI chat
    completions API format.
    """

    def __init__(
        self,
        api_key_env_var: str = "OPENAI_API_KEY",
        base_url: str | None = None,
        use_caching: bool = False,
    ):
        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            raise ValueError(
                f"API key not found in environment variable '{api_key_env_var}'. "
                f"Set it and restart."
            )

        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self._client = OpenAI(**kwargs)
        self.use_caching = use_caching and CURRENT_MODE in ("ACTOR", "AUTONOMY")

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
            content: list[dict] = []
            if msg.content:
                content.append({"type": "text", "text": msg.content})
            if msg.images:
                for img_b64 in msg.images:
                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_b64}",
                            },
                        }
                    )
            if len(content) == 1:
                api_messages.append({"role": role, "content": content[0]["text"]})
            else:
                api_messages.append({"role": role, "content": content})

        if self.use_caching and api_messages:
            last_content = api_messages[-1].get("content", "")
            if isinstance(last_content, list) and last_content:
                last_content[-1]["cache_control"] = {"type": "ephemeral"}
            elif not isinstance(last_content, list) and api_messages[-1]["content"]:
                api_messages[-1]["content"] = [
                    {"type": "text", "text": api_messages[-1]["content"]},
                ]
                api_messages[-1]["content"][-1]["cache_control"] = {"type": "ephemeral"}

        call_kwargs = {
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 4096,
        }

        if system_prompt:
            if self.use_caching:
                call_kwargs["messages"].insert(
                    0,
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "text",
                                "text": system_prompt,
                                "cache_control": {"type": "ephemeral"},
                            }
                        ],
                    },
                )
            else:
                call_kwargs["messages"].insert(
                    0, {"role": "system", "content": system_prompt}
                )

        try:
            response = self._client.chat.completions.create(**call_kwargs)
        except Exception as e:
            logger.error(f"OpenAI-compatible API error: {e}")
            raise

        choice = response.choices[0]
        content = choice.message.content or ""
        thinking = getattr(choice.message, "reasoning_content", None)

        elapsed_time = int((time.monotonic() - timer_start) * 1000)

        return ChatResponse(
            content=content.strip(),
            thinking=thinking,
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            total_duration_ms=elapsed_time,
        )
