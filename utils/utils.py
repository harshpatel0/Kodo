import re
import json
import tiktoken

from utils.globals import AVAILABLE_INTERACTION_LAYERS


def strip_markdown_json(raw: str) -> str:
    """Extract JSON from markdown code fences, or return raw string stripped."""
    if not raw:
        return ""

    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw)
    if match:
        return match.group(1).strip()

    match_inline = re.search(r"`({.*?})`", raw)
    if match_inline:
        return match_inline.group(1).strip()

    return raw.strip()


def try_parse_json(raw: str):
    """Attempt to parse JSON, with common repair strategies for local model output."""
    cleaned = strip_markdown_json(raw)
    if not cleaned:
        return None, "Empty response"

    last_error = None
    for strategy in (
        lambda s: s,
        lambda s: re.sub(r",\s*([}\]])", r"\1", s),
        lambda s: re.sub(
            r"(?<!\\)\b(null|true|false)\b", lambda m: m.group(1).lower(), s
        ),
    ):
        try:
            return json.loads(strategy(cleaned)), None
        except json.JSONDecodeError as e:
            last_error = e

    return None, f"Could not parse JSON: {last_error}"


def estimate_tokens(text) -> int:
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


from settings.settings import settings


def check_layer(
    layer: str,
) -> bool:
    try:
        return getattr(settings.interactions, layer, True)
    except AttributeError:
        return True


def config_guard() -> None:
    from utils.logger import logger

    active_provider = getattr(settings, "active_model_provider", "ollama")

    provider_cfg = None
    if hasattr(settings, "model_providers"):
        provider_cfg = getattr(settings.model_providers, active_provider, None)

    global_caching = getattr(settings, "caching", None)
    global_caching_enabled = (
        getattr(global_caching, "enabled", False) if global_caching else False
    )

    use_caching = False
    if provider_cfg:
        use_caching = getattr(provider_cfg, "use_caching", global_caching_enabled)
    else:
        use_caching = global_caching_enabled

    if not use_caching:
        if hasattr(settings, "context_provider") and getattr(
            settings.context_provider, "use_diffing", False
        ):
            logger.warning(
                "Config Guard: Caching is disabled, but context_provider.use_diffing was True. "
                "Automatically setting context_provider.use_diffing to False to prevent stateless coordinate loss."
            )
            settings.context_provider.use_diffing = False

        if hasattr(settings, "direct_app_control") and getattr(
            settings.direct_app_control, "use_diffing", False
        ):
            logger.warning(
                "Config Guard: Caching is disabled, but direct_app_control.use_diffing was True. "
                "Automatically setting direct_app_control.use_diffing to False to prevent stateless coordinate loss."
            )
            settings.direct_app_control.use_diffing = False

        enabled_layers = 0

    for layer in AVAILABLE_INTERACTION_LAYERS:
        if check_layer(layer):
            enabled_layers += 1

    if enabled_layers == 0:
        print("At least one interaction layer needs to be enabled for Kodo to work")
        exit(1)
