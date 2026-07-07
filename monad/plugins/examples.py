"""Example plugins bundled with Monad — HealthPlugin & SystemInfoPlugin."""

from __future__ import annotations

import platform
import time

import psutil

from monad.core.logger import get_logger
from monad.plugins.manager import Plugin

log = get_logger(__name__)


class HealthPlugin(Plugin):
    id = "health"
    name = "Health Monitor"
    version = "1.0.0"
    description = "Reports application uptime and simple health metrics."

    def __init__(self) -> None:
        self._loaded_at: float = 0.0

    def on_load(self) -> None:
        self._loaded_at = time.time()
        log.debug("HealthPlugin loaded")

    def on_unload(self) -> None:
        log.debug("HealthPlugin unloaded (was up {:.1f}s)", time.time() - self._loaded_at)

    def health(self) -> dict:
        return {
            "uptime_s": round(time.time() - self._loaded_at, 1),
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "ram_percent": psutil.virtual_memory().percent,
        }


class SystemInfoPlugin(Plugin):
    id = "system_info"
    name = "System Info"
    version = "1.0.0"
    description = "Reports host system information."

    def on_load(self) -> None:
        log.debug("SystemInfoPlugin loaded")

    def on_unload(self) -> None:
        log.debug("SystemInfoPlugin unloaded")

    def info_snapshot(self) -> dict:
        return {
            "os": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python": platform.python_version(),
            "cpu_cores": psutil.cpu_count(logical=True),
            "ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        }
