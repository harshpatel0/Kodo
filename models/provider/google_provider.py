import os
import base64
import time
import hashlib

from .base import ModelProvider, ChatMessage, ChatResponse, determine_caching
from utils.logger import logger
from settings.settings import settings


def _extract_status_code(err: Exception) -> int | None:
    for attr in ("code", "status_code", "grpc_status_code"):
        val = getattr(err, attr, None)
        if isinstance(val, int):
            return val
    msg = str(err).lower()
    for code_str, code_val in [
        ("503", 503),
        ("unavailable", 503),
        ("429", 429),
        ("400", 400),
    ]:
        if code_str in msg:
            return code_val
    return None


class GoogleProvider(ModelProvider):
    """Provider for Google Gemini models. Uses google-genai SDK.
    Reads API key from environment variable at init time.
    """

    def __init__(
        self,
        api_key_env_var: str = "GOOGLE_API_KEY",
        use_caching: bool = False,
        cache_ttl_seconds: int = 300,
    ):
        try:
            from google import genai
        except ImportError:
            raise ImportError(
                "google-genai is not installed. Run: pip install google-genai"
            )

        api_key = os.environ.get(api_key_env_var)
        if not api_key:
            raise ValueError(
                f"Google AI API key not found in environment variable '{api_key_env_var}'. "
                f"Set it and restart."
            )

        self._client = genai.Client(api_key=api_key)
        self._genai = genai
        self.use_caching = determine_caching(use_caching)
        self._cache_ttl = cache_ttl_seconds
        self._cached_contents: dict[str, tuple[str, float]] = {}

        if self.use_caching:
            self._clear_existing_caches()

    def _clear_existing_caches(self):
        try:
            for cached in self._client.caches.list():
                try:
                    self._client.caches.delete(name=cached.name)
                    logger.debug(f"Deleted stale cached content: {cached.name}")
                except Exception:
                    pass
        except Exception as e:
            logger.debug(f"No existing caches to clear: {e}")

    def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        temperature: float,
        max_tokens: int | None = None,
        **kwargs,
    ) -> ChatResponse:
        from google.genai import types

        timer_start = time.monotonic()

        system_prompt = None
        history = []

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
                continue

            parts = []
            if msg.content:
                parts.append(types.Part.from_text(text=msg.content))
            if msg.images:
                for img_b64 in msg.images:
                    image_bytes = base64.b64decode(img_b64)
                    parts.append(
                        types.Part.from_bytes(data=image_bytes, mime_type="image/png")
                    )

            role = "model" if msg.role == "assistant" else "user"
            history.append(types.Content(role=role, parts=parts))

        if not history:
            raise ValueError("No user/assistant messages provided.")

        config_kwargs = {"temperature": temperature}
        if max_tokens:
            config_kwargs["max_output_tokens"] = max_tokens

        cached_name = None
        if self.use_caching and system_prompt:
            cache_key = hashlib.sha256(
                (model + "||" + system_prompt).encode()
            ).hexdigest()
            now = time.time()
            entry = self._cached_contents.get(cache_key)
            if entry is not None and entry[1] > now:
                cached_name = entry[0]
            else:
                try:
                    from google.genai import types as _gtypes

                    cache_contents = history[:1] if history else []
                    cached_obj = self._client.caches.create(
                        model=model,
                        config=_gtypes.CreateCachedContentConfig(
                            system_instruction=system_prompt,
                            contents=cache_contents,
                            ttl=f"{self._cache_ttl}s",
                            display_name=f"sysprompt_{cache_key[:12]}",
                        ),
                    )
                    cached_name = cached_obj.name
                    self._cached_contents[cache_key] = (
                        cached_name,
                        now + self._cache_ttl,
                    )
                    if cache_contents:
                        history[:] = history[1:]
                except Exception as e:
                    logger.warning(
                        f"Failed to create Google cached content, falling back to normal request: {e}"
                    )

        if cached_name:
            config_kwargs["cached_content"] = cached_name
        elif system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        if kwargs.get("thinking", False):
            config_kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_budget=-1, include_thoughts=True
            )

        config = types.GenerateContentConfig(**config_kwargs)

        last_error = None
        for attempt in range(3):
            try:
                response = self._client.models.generate_content(
                    model=model,
                    contents=history,
                    config=config,
                )
                break
            except Exception as e:
                last_error = e
                status_code = _extract_status_code(e)
                if status_code == 503:
                    logger.warning(
                        f"Google AI is temporarily unavailable, the model might be in high demand and currenly unavailable."
                        f"Waiting 60 seconds before retry (attempt {attempt+1}/3)..."
                    )
                    time.sleep(60)
                    continue
                if status_code == 429:
                    logger.warning(
                        f"Google AI API rate limit exceeded. Waiting 10 seconds before retry (attempt {attempt+1}/3)..."
                    )
                    time.sleep(10)
                    continue
                logger.error(
                    f"Google AI API error (HTTP {status_code or 'unknown'}): {e}"
                )
                raise
        else:
            raise last_error or RuntimeError("Google AI request failed after 3 retries")

        try:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
        except Exception:
            input_tokens = output_tokens = 0

        global_caching = getattr(settings, "caching", None)
        if global_caching and getattr(global_caching, "log_stats", False):
            logger.info(
                f"Cache Control: {response.usage_metadata.cached_content_token_count}"
            )

        text = ""
        thinking = ""

        for part in response.candidates[0].content.parts:
            if part.thought:
                thinking = part.text
            else:
                text += part.text

        text = text.strip()

        if thinking:
            logger.debug(f"[GoogleProvider] Reasoning:\n{thinking}")

        elapsed_time = int((time.monotonic() - timer_start) * 1000)

        return ChatResponse(
            content=text,
            thinking=thinking if thinking != "" else None,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_duration_ms=elapsed_time,
        )
