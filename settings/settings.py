import json
from types import SimpleNamespace
from typing import Any

from settings.default import default_settings


class Settings:
    orchestrator: Any
    context_provider: Any
    models: Any
    model_providers: Any

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.load_settings()

    def load_settings(self) -> None:
        self.data = self._load_settings_from_file()
        self._parse_settings(self, self.data)

    def load_custom_settings(self, data: dict) -> None:
        self._parse_settings(self, data=data)

    def _load_settings_from_file(self) -> dict:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = default_settings
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return data

        missing_keys = [key for key in default_settings if key not in data]

        if missing_keys:
            print(
                f"[Settings] Warning: settings.json is missing keys: {missing_keys}. "
                "Filling in from defaults."
            )
            for key in missing_keys:
                data[key] = default_settings[key]
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        return data

    def _parse_settings(self, obj, data: dict) -> None:
        for key, value in data.items():
            if isinstance(value, dict):
                nested_obj = SimpleNamespace()
                setattr(obj, key, nested_obj)
                self._parse_settings(nested_obj, value)
            else:
                setattr(obj, key, value)

    def reload_settings(self) -> None:
        self.load_settings()


settings = Settings("settings.json")
