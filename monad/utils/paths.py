"""Path helpers."""

from __future__ import annotations

import os
from pathlib import Path


def get_monad_root() -> Path:
    """Return the Monad root directory (env var overrides auto-detection)."""
    override = os.environ.get("MONAD_ROOT")
    if override:
        return Path(override).resolve()
    # Walk up from this file: monad/utils/paths.py -> monad/utils -> monad -> root
    return Path(__file__).resolve().parents[2]
