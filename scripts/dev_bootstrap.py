"""
Quick bootstrap script for developers:
  - Creates .venv
  - Installs project in editable mode with dev extras
  - Prints next steps

Run from repo root:
    python scripts/dev_bootstrap.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd, **kw):
    print(f"$ {' '.join(cmd)}")
    subprocess.check_call(cmd, cwd=ROOT, **kw)


def main():
    venv = ROOT / ".venv"
    if not venv.exists():
        print("Creating venv…")
        run([sys.executable, "-m", "venv", str(venv)])
    py = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    print("Installing dependencies…")
    run([str(py), "-m", "pip", "install", "-U", "pip"])
    run([str(py), "-m", "pip", "install", "-e", ".[dev]"])
    print()
    print("Done!")
    print(f"  Activate:  {venv}\\Scripts\\activate  (Windows)")
    print(f"             source {venv}/bin/activate  (Linux/Mac)")
    print("  Run tests: pytest")
    print("  Start:     python run.py")


if __name__ == "__main__":
    main()
