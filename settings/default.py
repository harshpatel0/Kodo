default_settings = {
    "active_model_provider": "ollama",
    "caching": {
        "enabled": False,
        "ttl_seconds": 300,
        "log_stats": False,
    },
    "model_providers": {
        "ollama": {
            "server_url": "localhost:11434",
            "timeout": 120,
        },
        "anthropic": {
            "api_key_env_var": "ANTHROPIC_API_KEY",
            "base_url": None,
            "effort": "medium",
            "use_caching": False,
        },
        "google": {
            "api_key_env_var": "GOOGLE_API_KEY",
            "use_caching": False,
            "cache_ttl_seconds": 300,
        },
        "openai_compatible": {
            "api_key_env_var": "OPENAI_COMPATIBLE_API_KEY",
            "base_url": None,
            "use_caching": False,
        },
    },
    "models": {
        "skill_installation": {
            "provider": "ollama",
            "model_name": "gemma4:e4b",
            "temperature": 0.1,
            "keep_alive": 0,
        },
        "planner": {
            "provider": "ollama",
            "model_name": "gemma4:e4b",
            "thinking": True,
            "temperature": 0.7,
            "keep_alive": 0,
        },
        "actor": {
            "provider": "ollama",
            "model_name": "gemma4:e4b",
            "thinking": True,
            "temperature": 0.3,
            "keep_alive": 30,
            "attach_screenshot_of_active_window": True,
        },
        "autonomy_actor": {
            "provider": "ollama",
            "model_name": "gemma4:e4b",
            "thinking": True,
            "temperature": 0.5,
            "keep_alive": 150,
            "attach_screenshot_of_active_window": True,
        },
    },
    "interactions": {
        "direct_app_control": True,
        "mcps": True,
        "pc_actions": True,
        "python": True,
        "skills": True,
        "no_skill_installation_mode": True,
    },
    "orchestrator": {
        "action_settle_time": 4,
        "use_autonomy_mode": True,
        "planner_architecture": {
            "max_iterations_per_step": 10,
            "max_autonomy_steps": 10,
            "max_replan_loop": 7,
        },
        "autonomy_orchestrator": {
            "max_total_iterations": 50,
            "toast_notify_history": False,
        },
    },
    "context_provider": {
        "waiting_period": 4,
        "skip_after_ticks": 10,
        "take_full_screen_screenshot": True,
        "screenshot_quality_percentage": 80,
        "provide_uia_tree": True,
        "use_diffing": True,
    },
    "skills": {
        "skill_timeout": 0,
    },
    "direct_app_control": {"always_populate_connected_app_controls": True, "use_diffing": True},
    "web_ui": {
        "expose_web_ui_to_all_devices_on_the_network": False,
        "desktop_streaming_quality_percentage": 85,
        "desktop_streaming_frame_rate": 30,
    },
    "log_to_file": True,
}
