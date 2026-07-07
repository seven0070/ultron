"""
Build #006 — Core Application Manager.

Singleton orchestrator that runs startup/shutdown sequences and holds
application-wide state.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from monad import __codename__, __version__
from monad.config import ConfigManager
from monad.core.container import ServiceContainer
from monad.core.environment import EnvironmentManager, EnvironmentReport
from monad.core.logger import LoggerManager, get_logger
from monad.core.resource_manager import ResourceManager

log = get_logger(__name__)


@dataclass
class ApplicationState:
    started_at: float = 0.0
    ready: bool = False
    env_report: EnvironmentReport | None = None
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class MonadApplication:
    """Singleton Monad application. Wires up all core subsystems."""

    _instance: "MonadApplication | None" = None

    def __new__(cls, *args, **kwargs) -> "MonadApplication":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, root: Path | None = None) -> None:
        if getattr(self, "_initialized", False):
            return
        self.root: Path = (root or Path.cwd()).resolve()
        self.state = ApplicationState()
        self.container = ServiceContainer()
        self.config: ConfigManager | None = None
        self.resources: ResourceManager | None = None
        self._initialized = True

    # -- lifecycle ------------------------------------------------------------

    def startup(self, banner: bool = True) -> ApplicationState:
        """Run the full startup sequence."""
        self.state.started_at = time.time()

        # 1. Config first (no logger yet — config errors go to stderr)
        self.config = ConfigManager(self.root / "config.yaml")
        self.config.load()

        # 2. Resource manager
        self.resources = ResourceManager(
            root=self.root,
            paths_config=self.config.get("paths", {}),
        )
        self.resources.ensure_directories()

        # 3. Logger
        log_cfg = self.config.get("logging", {})
        LoggerManager().configure(
            logs_dir=self.resources.logs_dir,
            level=log_cfg.get("level", "INFO"),
            console=log_cfg.get("console", True),
            file=log_cfg.get("file", True),
            rotation=log_cfg.get("file_rotation", "10 MB"),
            retention=log_cfg.get("file_retention", "7 days"),
            compact=log_cfg.get("format_compact", False),
        )

        if banner:
            self._print_banner()

        log.info("Monad application starting up (root={})", self.root)

        # 4. Environment check
        env_mgr = EnvironmentManager()
        self.state.env_report = env_mgr.report()
        for w in self.state.env_report.warnings:
            log.warning(w)
            self.state.warnings.append(w)
        for e in self.state.env_report.errors:
            log.error(e)
            self.state.errors.append(e)

        # 5. Register core services in DI container
        self.container.register_singleton("config", self.config)
        self.container.register_singleton("resources", self.resources)
        self.container.register_singleton("environment", env_mgr)
        self.container.register_singleton("logger_manager", LoggerManager())

        # 6. Load auto plugins (Build #008)
        try:
            from monad.plugins import PluginManager
            plugin_mgr = PluginManager()
            plugin_mgr.discover_and_load(
                auto_load=self.config.get("plugins.auto_load", []),
            )
            self.container.register_singleton("plugin_manager", plugin_mgr)
        except Exception as e:
            log.warning("Plugin loading skipped: {}", e)

        self.state.ready = not self.state.errors
        elapsed = time.time() - self.state.started_at
        log.success("Monad ready in {:.2f}s (ready={})", elapsed, self.state.ready)
        return self.state

    def shutdown(self) -> None:
        log.info("Monad shutting down…")
        # Placeholder for future cleanup (unload models, flush memory, etc.)
        self.state.ready = False
        log.success("Monad shutdown complete.")

    # -- health ---------------------------------------------------------------

    def health_check(self) -> dict:
        return {
            "ready": self.state.ready,
            "uptime_s": round(time.time() - self.state.started_at, 1),
            "errors": self.state.errors,
            "warnings": self.state.warnings,
            "env": self.state.env_report.to_dict() if self.state.env_report else None,
            "resources": self.resources.summary() if self.resources else None,
        }

    # -- misc -----------------------------------------------------------------

    def _print_banner(self) -> None:
        banner = rf"""
    ███╗   ███╗ ██████╗ ███╗   ██╗ █████╗ ██████╗
    ████╗ ████║██╔═══██╗████╗  ██║██╔══██╗██╔══██╗
    ██╔████╔██║██║   ██║██╔██╗ ██║███████║██║  ██║
    ██║╚██╔╝██║██║   ██║██║╚██╗██║██╔══██║██║  ██║
    ██║ ╚═╝ ██║╚██████╔╝██║ ╚████║██║  ██║██████╔╝
    ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝╚═════╝
    ── codename: {__codename__} ─ v{__version__} ─ portable local AI ──
        """
        print(banner)
