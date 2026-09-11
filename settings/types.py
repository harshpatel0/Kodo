"""Type-only shape declarations for settings.json.

These classes are never instantiated. `Settings._parse_settings` still builds the real
objects dynamically as `SimpleNamespace` trees at runtime -- these classes exist purely so
the type checker (and your editor's autocomplete) knows what fields exist on `settings.<x>`.

Keep these in sync with `settings/default.py` by hand: add/rename/remove a field here
whenever you add/rename/remove one there. Nothing will fail if they drift -- you'll just
lose (or get wrong) autocomplete until you fix it.
"""

from typing import Optional


class CachingSettings:
    log_stats: bool
    enabled: bool
    ttl_seconds: int


class OllamaProviderSettings:
    server_url: str
    timeout: int


class AnthropicProviderSettings:
    api_key_env_var: str
    base_url: Optional[str]
    effort: str
    use_caching: bool


class GoogleProviderSettings:
    api_key_env_var: str
    use_caching: bool
    cache_ttl_seconds: int


class OpenAICompatibleProviderSettings:
    api_key_env_var: str
    base_url: Optional[str]
    use_caching: bool


class ModelProvidersSettings:
    ollama: OllamaProviderSettings
    anthropic: AnthropicProviderSettings
    google: GoogleProviderSettings
    openai_compatible: OpenAICompatibleProviderSettings


class SkillInstallationModelSettings:
    provider: str
    model_name: str
    temperature: float
    keep_alive: int


class AutonomyActorModelSettings:
    provider: str
    model_name: str
    thinking: bool
    temperature: float
    keep_alive: int
    attach_screenshot_of_active_window: bool


class ModelsSettings:
    skill_installation: SkillInstallationModelSettings
    autonomy_actor: AutonomyActorModelSettings


class InteractionsSettings:
    direct_app_control: bool
    mcps: bool
    pc_actions: bool
    python: bool
    skills: bool
    no_skill_installation_mode: bool
    daemons: bool


class AutonomyOrchestratorSettings:
    max_total_iterations: int
    toast_notify_history: bool


class OrchestratorSettings:
    action_settle_time: float
    max_replan_loop: int
    autonomy_orchestrator: AutonomyOrchestratorSettings


class ContextProviderSettings:
    waiting_period: int
    skip_after_ticks: int
    take_full_screen_screenshot: bool
    screenshot_quality_percentage: int
    provide_uia_tree: bool
    use_diffing: bool


class SkillsSettings:
    # skill_timeout is the only statically-known field. Individual skills may add their own
    # block keyed by skill name (e.g. "browser-navigation"), which usually isn't a valid
    # Python identifier -- read those with getattr(settings.skills, "skill-name", None)
    # rather than dot access, and don't add them here.
    skill_timeout: int


class DirectAppControlSettings:
    always_populate_connected_app_controls: bool
    use_diffing: bool


class WebUISettings:
    expose_web_ui_to_all_devices_on_the_network: bool
    desktop_streaming_quality_percentage: int
    desktop_streaming_frame_rate: int


class TrayAppSettings:
    width_percentage: int
    height_percentage: int
    expanded_width_percentage: int
    expanded_height_percentage: int
    x_position_percentage: int
    y_position_percentage: int
    web_ui_port: int
