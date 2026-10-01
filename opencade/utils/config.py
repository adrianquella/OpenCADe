"""Configuration settings for opencade.

A singleton-style container with dot-notation access, for example::

    from opencade.utils.config import config
    step = config.get("simulation.time_step")
    config.set("simulation.time_step", 0.005)
"""

import json
import os
from typing import Any, Dict


class Config:
    """Global configuration of the application (singleton)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._settings: Dict[str, Any] = {
                "simulation": {
                    "time_step": 0.01,  # s
                    "max_realtime_factor": 100.0,
                },
                "pneumatic": {
                    "default_pressure": 6.0e5,  # Pa gauge (typical 6 bar)
                    "atmospheric_pressure": 101325.0,  # Pa
                    "air_density": 1.2,  # kg/m^3
                },
                "electrical": {
                    "default_voltage": 24.0,  # V (control circuits)
                    "default_frequency": 50.0,  # Hz
                },
                "gui": {
                    "theme": "default",
                    "grid_size": 10,  # px
                    "snap_to_grid": True,
                },
            }
        return cls._instance

    def get(self, key: str, default: Any = None) -> Any:
        """Fetch a value using a dotted key (e.g. "simulation.time_step")."""
        value: Any = self._settings
        for part in key.split("."):
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a value using a dotted key (missing intermediate dicts are created)."""
        parts = key.split(".")
        target = self._settings
        for part in parts[:-1]:
            child = target.get(part)
            if not isinstance(child, dict):
                child = {}
                target[part] = child
            target = child
        target[parts[-1]] = value

    def load_from_file(self, filepath: str) -> None:
        """Merge a JSON configuration file into the current settings."""
        with open(filepath, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            raise ValueError(f"Invalid configuration file: {filepath}")
        self._deep_update(self._settings, data)

    def save_to_file(self, filepath: str) -> None:
        """Write the current settings to a JSON file."""
        directory = os.path.dirname(os.path.abspath(filepath))
        os.makedirs(directory, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as handle:
            json.dump(self._settings, handle, indent=2)

    @staticmethod
    def _deep_update(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively merge *override* into *base*."""
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(base.get(key), dict):
                Config._deep_update(base[key], value)
            else:
                base[key] = value
        return base


#: Global configuration instance shared across the application.
config = Config()
