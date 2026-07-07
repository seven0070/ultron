"""
Build #003 — YAML configuration manager.

Loads config.yaml, validates required sections, and exposes dotted-path access.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigError(Exception):
    """Raised on config load/validate failures."""


class ConfigManager:
    """Loads and validates the main YAML config."""

    REQUIRED_SECTIONS = ("application", "paths", "runtime", "logging")

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._data: dict[str, Any] = {}
        self._loaded = False

    # -- load / validate ------------------------------------------------------

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            raise ConfigError(f"Config file not found: {self.path}")

        try:
            with self.path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {self.path}: {e}") from e

        if not isinstance(data, dict):
            raise ConfigError(f"Config root must be a mapping, got {type(data).__name__}")

        self._data = data
        self._validate()
        self._loaded = True
        return self._data

    def _validate(self) -> None:
        missing = [s for s in self.REQUIRED_SECTIONS if s not in self._data]
        if missing:
            raise ConfigError(f"Missing required config sections: {missing}")

    # -- access ---------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Dotted-path lookup: `cfg.get('logging.level', 'INFO')`."""
        node: Any = self._data
        for part in key.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def require(self, key: str) -> Any:
        val = self.get(key, None)
        if val is None:
            raise ConfigError(f"Required config key missing: {key}")
        return val

    def all(self) -> dict[str, Any]:
        return dict(self._data)

    @property
    def loaded(self) -> bool:
        return self._loaded

    def __repr__(self) -> str:
        return f"ConfigManager(path={self.path}, loaded={self._loaded})"
