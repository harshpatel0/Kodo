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


from utils.toasts.toast import toaster


def config_guard() -> None:
    from utils.logger import logger

    use_autonomy_mode = getattr(
        getattr(settings, "orchestrator", None), "use_autonomy_mode", False
    )
    driving_role = "autonomy_actor" if use_autonomy_mode else "actor"

    role_cfg = getattr(getattr(settings, "models", None), driving_role, None)
    role_provider_name = getattr(role_cfg, "provider", None) if role_cfg else None

    use_caching = False
    if role_provider_name and hasattr(settings, "model_providers"):
        provider_cfg = getattr(settings.model_providers, role_provider_name, None)
        use_caching = (
            getattr(provider_cfg, "use_caching", False) if provider_cfg else False
        )
    else:
        logger.warning(
            f"Config Guard: could not resolve a provider for models.{driving_role} "
            "(missing 'provider' field?). Treating caching as disabled for the "
            "diffing safety check below."
        )

    if not use_caching:
        if hasattr(settings, "context_provider") and getattr(
            settings.context_provider, "use_diffing", False
        ):
            logger.warning(
                f"Config Guard: caching is disabled for models.{driving_role} "
                f"(provider: {role_provider_name}), but context_provider.use_diffing was True. "
                "Automatically setting context_provider.use_diffing to False to prevent stateless coordinate loss."
            )
            settings.context_provider.use_diffing = False

            toaster.update(
                "Mitigated Configuration Violation",
                f"Caching is disabled for {driving_role.title()}, so diffing was disabled for context provider. This run may use more tokens",
            )

        if hasattr(settings, "direct_app_control") and getattr(
            settings.direct_app_control, "use_diffing", False
        ):
            logger.warning(
                f"Config Guard: caching is disabled for models.{driving_role} "
                f"(provider: {role_provider_name}), but direct_app_control.use_diffing was True. "
                "Automatically setting direct_app_control.use_diffing to False to prevent stateless coordinate loss."
            )
            settings.direct_app_control.use_diffing = False

            toaster.update(
                "Mitigated Configuration Violation",
                f"Caching is disabled for {driving_role.title()}, so diffing was disabled for DAC Context Provider. This run may use more tokens",
            )

    enabled_layers = 0
    for layer in AVAILABLE_INTERACTION_LAYERS:
        if check_layer(layer):
            enabled_layers += 1

    if enabled_layers == 0:
        print(
            "At least one interaction layer needs to be enabled for Kodo to work",
        )
        toaster.update(
            "Failed to start Kodo",
            f"At least one interaction layer needs to be enabled for Kodo to work",
        )
        exit(1)
