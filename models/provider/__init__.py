"""Model provider abstraction layer.

Usage:
    from models.provider import get_provider, ChatMessage, ChatResponse

    provider = get_provider(model_config)
    response = provider.chat(
        messages=[ChatMessage(role="user", content="Hello")],
        model="gemma4:e4b",
        temperature=0.7,
    )
"""

from .base import ModelProvider, ChatMessage, ChatResponse
from .ollama_provider import OllamaProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from .openai_compatible_provider import OpenAICompatibleProvider
from settings.settings import settings

_PROVIDER_CACHE: dict[str, ModelProvider] = {}


def get_provider(model_config):
    """Get or create a ModelProvider instance.

    Args:
        model_config: A SimpleNamespace with a required `provider` field
                      (e.g. settings.models.actor).

    Returns:
        A ModelProvider instance (OllamaProvider, AnthropicProvider, or GoogleProvider).

    Raises:
        ValueError: if model_config is missing or has no `provider` set
    """
    provider_name = getattr(model_config, "provider", None) if model_config else None
    if not provider_name:
        raise ValueError(
            "get_provider() requires model_config.provider to be set explicitly "
        )

    factory_map = {
        "ollama": _create_ollama_provider,
        "anthropic": _create_anthropic_provider,
        "google": _create_google_provider,
        "openai-compatible": _create_openai_compatible_provider,
    }

    if provider_name not in factory_map:
        raise ValueError(
            f"Unknown model provider '{provider_name}'. "
            f"Available: {', '.join(factory_map.keys())}"
        )

    if provider_name not in _PROVIDER_CACHE:
        _PROVIDER_CACHE[provider_name] = factory_map[provider_name]()

    return _PROVIDER_CACHE[provider_name]


def clear_provider_cache():
    _PROVIDER_CACHE.clear()


def _get_use_caching(provider_cfg) -> bool:
    return getattr(provider_cfg, "use_caching", False)


def _get_cache_ttl(provider_cfg) -> int:
    return getattr(provider_cfg, "cache_ttl_seconds", 300)


def _create_ollama_provider() -> OllamaProvider:
    cfg = settings.model_providers.ollama
    return OllamaProvider(
        server_url=getattr(cfg, "server_url", "localhost:11434"),
        timeout=getattr(cfg, "timeout", 120),
    )


def _create_anthropic_provider() -> AnthropicProvider:
    cfg = settings.model_providers.anthropic
    return AnthropicProvider(
        api_key_env_var=getattr(cfg, "api_key_env_var", "ANTHROPIC_API_KEY"),
        base_url=getattr(cfg, "base_url", None),
        use_caching=_get_use_caching(cfg),
    )


def _create_google_provider() -> GoogleProvider:
    cfg = settings.model_providers.google
    return GoogleProvider(
        api_key_env_var=getattr(cfg, "api_key_env_var", "GOOGLE_API_KEY"),
        use_caching=_get_use_caching(cfg),
        cache_ttl_seconds=_get_cache_ttl(cfg),
    )


def _create_openai_compatible_provider() -> OpenAICompatibleProvider:
    cfg = settings.model_providers.openai_compatible
    return OpenAICompatibleProvider(
        api_key_env_var=getattr(cfg, "api_key_env_var", "OPENAI_COMPATIBLE_API_KEY"),
        base_url=getattr(cfg, "base_url", None),
        use_caching=_get_use_caching(cfg),
    )
