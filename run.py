"""
Monad-Ultron — Main entry point.

Usage:
    python run.py                 # Start Monad (default: launch CLI)
    python run.py --help          # Show all commands
    python run.py start           # Start interactive session
    python run.py status          # Show system status
    python run.py doctor          # Diagnose environment
    python run.py chat            # Enter chat mode
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the package is importable when run directly from source
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from monad.ui.cli import app  # noqa: E402


def main() -> None:
    """Entry point invoked by `python run.py` or the `monad` script."""
    app()


if __name__ == "__main__":
    main()
