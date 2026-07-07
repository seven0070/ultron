"""
Build #007 — Resource Manager.

Owns all filesystem paths, detects whether we're running from a USB (removable
disk), and reports disk health.
"""

from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass
from pathlib import Path

from monad.core.logger import get_logger

log = get_logger(__name__)


@dataclass
class DiskHealth:
    path: Path
    total_gb: float
    free_gb: float
    used_gb: float
    percent_used: float
    writable: bool


class ResourceManager:
    """Singleton that manages all Monad filesystem paths."""

    _instance: "ResourceManager | None" = None

    def __new__(cls, *args, **kwargs) -> "ResourceManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, root: Path, paths_config: dict[str, str] | None = None) -> None:
        # Avoid re-initialization on singleton re-instantiation
        if getattr(self, "_initialized", False):
            return

        self.root: Path = Path(root).resolve()
        cfg = paths_config or {}

        self.models_dir: Path = self._resolve(cfg.get("models_dir", "models"))
        self.memory_dir: Path = self._resolve(cfg.get("memory_dir", "memory_data"))
        self.workspace_dir: Path = self._resolve(cfg.get("workspace_dir", "workspace"))
        self.logs_dir: Path = self._resolve(cfg.get("logs_dir", "logs"))
        self.cache_dir: Path = self._resolve(cfg.get("cache_dir", "cache"))
        self.config_dir: Path = self._resolve(cfg.get("config_dir", "config"))
        self.plugins_dir: Path = self._resolve(cfg.get("plugins_dir", "monad/plugins"))

        self._initialized = True

    # -- helpers --------------------------------------------------------------

    def _resolve(self, p: str | Path) -> Path:
        path = Path(p)
        return path if path.is_absolute() else (self.root / path)

    def ensure_directories(self) -> None:
        """Create all managed directories if they don't exist."""
        for d in [
            self.models_dir,
            self.memory_dir,
            self.workspace_dir,
            self.logs_dir,
            self.cache_dir,
            self.config_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)
        log.debug("Ensured Monad directories under {}", self.root)

    # -- USB / disk detection -------------------------------------------------

    def is_running_from_usb(self) -> bool:
        """Best-effort detection of removable storage on Windows."""
        if platform.system() != "Windows":
            return False
        try:
            import ctypes

            drive = str(self.root.drive).rstrip("\\").rstrip("/") + "\\"
            DRIVE_REMOVABLE = 2
            return ctypes.windll.kernel32.GetDriveTypeW(drive) == DRIVE_REMOVABLE
        except Exception as e:
            log.debug("USB detection failed: {}", e)
            return False

    def disk_health(self, path: Path | None = None) -> DiskHealth:
        """Report free/used disk on the volume containing `path` (default: root)."""
        target = path or self.root
        usage = shutil.disk_usage(target)
        total_gb = usage.total / (1024**3)
        free_gb = usage.free / (1024**3)
        used_gb = usage.used / (1024**3)
        percent = (used_gb / total_gb * 100) if total_gb else 0.0

        # writability probe
        writable = True
        try:
            probe = target / ".monad_write_test"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
        except Exception:
            writable = False

        return DiskHealth(
            path=target,
            total_gb=round(total_gb, 2),
            free_gb=round(free_gb, 2),
            used_gb=round(used_gb, 2),
            percent_used=round(percent, 1),
            writable=writable,
        )

    def summary(self) -> dict:
        return {
            "root": str(self.root),
            "on_usb": self.is_running_from_usb(),
            "paths": {
                "models": str(self.models_dir),
                "memory": str(self.memory_dir),
                "workspace": str(self.workspace_dir),
                "logs": str(self.logs_dir),
                "cache": str(self.cache_dir),
                "config": str(self.config_dir),
                "plugins": str(self.plugins_dir),
            },
        }
