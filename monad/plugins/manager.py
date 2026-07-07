"""
Build #008 — Plugin manager and Plugin ABC.

Discovers plugins, registers them, and controls enable/disable state.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from monad.core.logger import get_logger

log = get_logger(__name__)


class Plugin(ABC):
    """Abstract base for all Monad plugins."""

    id: str = ""
    name: str = ""
    version: str = "0.0.0"
    description: str = ""

    @abstractmethod
    def on_load(self) -> None: ...

    @abstractmethod
    def on_unload(self) -> None: ...

    def info(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
        }


@dataclass
class _Entry:
    plugin: Plugin
    enabled: bool = False


class PluginManager:
    """Manages plugin discovery, lifecycle, and enable/disable state."""

    _instance: "PluginManager | None" = None

    def __new__(cls) -> "PluginManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._plugins: dict[str, _Entry] = {}
        self._initialized = True

    # -- discovery ------------------------------------------------------------

    def register(self, plugin: Plugin) -> None:
        if not plugin.id:
            raise ValueError("Plugin.id must be set")
        if plugin.id in self._plugins:
            log.warning("Plugin '{}' already registered — replacing", plugin.id)
        self._plugins[plugin.id] = _Entry(plugin=plugin, enabled=False)
        log.debug("Registered plugin: {}", plugin.id)

    def discover_and_load(self, auto_load: list[str] | None = None) -> None:
        """Discover built-in plugins and auto-enable the requested ones."""
        # Import example plugins lazily to avoid circulars
        from monad.plugins.examples import HealthPlugin, SystemInfoPlugin

        for cls in (HealthPlugin, SystemInfoPlugin):
            self.register(cls())

        for pid in auto_load or []:
            if pid in self._plugins:
                self.enable(pid)
            else:
                log.warning("Plugin '{}' requested in auto_load but not found", pid)

    # -- lifecycle ------------------------------------------------------------

    def enable(self, plugin_id: str) -> None:
        entry = self._require(plugin_id)
        if entry.enabled:
            return
        entry.plugin.on_load()
        entry.enabled = True
        log.info("Plugin enabled: {}", plugin_id)

    def disable(self, plugin_id: str) -> None:
        entry = self._require(plugin_id)
        if not entry.enabled:
            return
        entry.plugin.on_unload()
        entry.enabled = False
        log.info("Plugin disabled: {}", plugin_id)

    def list_plugins(self) -> list[dict]:
        out = []
        for entry in self._plugins.values():
            info = entry.plugin.info()
            info["enabled"] = entry.enabled
            out.append(info)
        return out

    def get(self, plugin_id: str) -> Plugin | None:
        e = self._plugins.get(plugin_id)
        return e.plugin if e else None

    def _require(self, plugin_id: str) -> _Entry:
        if plugin_id not in self._plugins:
            raise KeyError(f"Unknown plugin: {plugin_id}")
        return self._plugins[plugin_id]
