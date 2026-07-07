"""
Build #004 — Logging system (Loguru-based).

Central logging singleton with console + rotating file output.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger as _loguru_logger


class LoggerManager:
    """Singleton wrapper around Loguru with console + file sinks."""

    _instance: "LoggerManager | None" = None
    _configured: bool = False

    def __new__(cls) -> "LoggerManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def configure(
        self,
        logs_dir: Path,
        level: str = "INFO",
        console: bool = True,
        file: bool = True,
        rotation: str = "10 MB",
        retention: str = "7 days",
        compact: bool = False,
    ) -> None:
        """Configure global logger. Idempotent — safe to call multiple times."""
        _loguru_logger.remove()

        if console:
            fmt = (
                "<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | "
                "<cyan>{name}</cyan> - <level>{message}</level>"
                if compact
                else "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level:<8}</level> | <cyan>{name}:{function}:{line}</cyan> | "
                "<level>{message}</level>"
            )
            _loguru_logger.add(sys.stderr, level=level, format=fmt, colorize=True)

        if file:
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = logs_dir / "monad_{time:YYYY-MM-DD}.log"
            _loguru_logger.add(
                str(log_file),
                level=level,
                rotation=rotation,
                retention=retention,
                encoding="utf-8",
                format=(
                    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
                    "{name}:{function}:{line} | {message}"
                ),
            )

        self._configured = True
        _loguru_logger.debug("LoggerManager configured (level={}, dir={})", level, logs_dir)

    @property
    def is_configured(self) -> bool:
        return self._configured


def get_logger(name: str | None = None):
    """Fetch a bound logger. Use in every module: `log = get_logger(__name__)`."""
    if name:
        return _loguru_logger.bind(name=name)
    return _loguru_logger
