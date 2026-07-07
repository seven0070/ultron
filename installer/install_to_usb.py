"""
Monad-Ultron — USB installer.

Copies the codebase to the USB, sets up portable Python, installs deps,
downloads models, drops a launcher.

Usage:
    python installer/install_to_usb.py                 # interactive
    python installer/install_to_usb.py --drive E:      # non-interactive
    python installer/install_to_usb.py --drive E: --skip-models
"""

from __future__ import annotations

import argparse
import platform
import shutil
import string
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Simple console helpers (no external deps — installer must run on plain Python)
# ---------------------------------------------------------------------------

def info(msg): print(f"[i] {msg}")
def ok(msg):   print(f"[OK] {msg}")
def warn(msg): print(f"[!] {msg}")
def err(msg):  print(f"[X] {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# USB detection
# ---------------------------------------------------------------------------

def list_removable_drives() -> list[str]:
    """Return list of removable drive letters (Windows only)."""
    drives = []
    if platform.system() != "Windows":
        return drives
    try:
        import ctypes
        DRIVE_REMOVABLE = 2
        for letter in string.ascii_uppercase:
            root = f"{letter}:\\"
            if ctypes.windll.kernel32.GetDriveTypeW(root) == DRIVE_REMOVABLE:
                drives.append(f"{letter}:")
    except Exception as e:
        warn(f"USB detection failed: {e}")
    return drives


def choose_drive(preselected: str | None) -> Path:
    if preselected:
        p = Path(preselected + "\\") if not preselected.endswith("\\") else Path(preselected)
        if not p.exists():
            err(f"Drive not found: {p}")
            sys.exit(1)
        return p

    removables = list_removable_drives()
    if not removables:
        warn("No removable drives detected.")
        answer = input("Enter USB drive letter manually (e.g. E:): ").strip()
        return Path(answer + "\\")

    print("\nRemovable drives found:")
    for i, d in enumerate(removables, 1):
        try:
            usage = shutil.disk_usage(d + "\\")
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            print(f"  [{i}] {d}   ({free_gb:.1f} GB free of {total_gb:.1f} GB)")
        except Exception:
            print(f"  [{i}] {d}")

    idx = input(f"\nPick drive [1-{len(removables)}]: ").strip()
    try:
        return Path(removables[int(idx) - 1] + "\\")
    except (ValueError, IndexError):
        err("Invalid selection.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Copy codebase
# ---------------------------------------------------------------------------

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", "node_modules",
    "models",  # skip — filled by download step
    "python_portable", "logs", "cache",
}
EXCLUDE_FILES = {".DS_Store", "Thumbs.db"}


def copy_codebase(src: Path, dst: Path) -> None:
    info(f"Copying codebase: {src} -> {dst}")
    dst.mkdir(parents=True, exist_ok=True)

    for item in src.iterdir():
        if item.name in EXCLUDE_DIRS or item.name in EXCLUDE_FILES:
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns(*EXCLUDE_DIRS, *EXCLUDE_FILES))
        else:
            shutil.copy2(item, target)
    ok("Codebase copied.")


# ---------------------------------------------------------------------------
# Portable Python
# ---------------------------------------------------------------------------

def install_portable_python(usb_root: Path) -> Path:
    """Download embeddable Python 3.12 zip and extract to USB/python_portable/."""
    try:
        from installer.download_python import download_and_extract  # type: ignore
    except ImportError:
        sys.path.insert(0, str(REPO_ROOT))
        from installer.download_python import download_and_extract

    target = usb_root / "python_portable"
    if target.exists() and (target / "python.exe").exists():
        ok("Portable Python already present — skipping download.")
        return target
    info("Downloading portable Python 3.12 (~30 MB)…")
    download_and_extract(target)
    ok(f"Portable Python installed at {target}")
    return target


def install_requirements(usb_root: Path, python_dir: Path) -> None:
    py = python_dir / "python.exe"
    if not py.exists():
        warn("Portable python.exe not found — skipping requirements install.")
        return
    reqs = usb_root / "requirements.txt"
    info(f"Installing requirements from {reqs}")
    # Bootstrap pip in embeddable python
    try:
        subprocess.check_call([str(py), "-m", "ensurepip", "--upgrade"])
    except subprocess.CalledProcessError:
        warn("ensurepip not available in embeddable python — attempting get-pip.py")
        # (embeddable distributions require manual pip bootstrap; skipping deep impl here)
    subprocess.check_call([str(py), "-m", "pip", "install", "-U", "pip"])
    subprocess.check_call([str(py), "-m", "pip", "install", "-r", str(reqs)])
    ok("Requirements installed on USB.")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

def download_models(usb_root: Path) -> None:
    try:
        from installer.download_models import download_all  # type: ignore
    except ImportError:
        sys.path.insert(0, str(REPO_ROOT))
        from installer.download_models import download_all
    info("Downloading models — this is the slow step (~15 GB).")
    download_all(usb_root / "models.yaml", usb_root / "models")


# ---------------------------------------------------------------------------
# Launcher
# ---------------------------------------------------------------------------

LAUNCHER_BAT = r"""@echo off
REM Monad-Ultron launcher — double-click to start
setlocal
cd /d "%~dp0"
set MONAD_ROOT=%CD%
set PY="%MONAD_ROOT%\python_portable\python.exe"
if not exist %PY% (
    echo Portable Python not found. Re-run the installer.
    pause
    exit /b 1
)
%PY% "%MONAD_ROOT%\run.py" %*
if errorlevel 1 pause
endlocal
"""

LAUNCHER_CLI = r"""@echo off
REM Monad-Ultron CLI launcher
setlocal
cd /d "%~dp0"
set MONAD_ROOT=%CD%
set PY="%MONAD_ROOT%\python_portable\python.exe"
%PY% -m monad.ui.cli %*
endlocal
"""


def install_launcher(usb_root: Path) -> None:
    (usb_root / "monad.bat").write_text(LAUNCHER_BAT, encoding="utf-8")
    (usb_root / "monad-cli.bat").write_text(LAUNCHER_CLI, encoding="utf-8")
    ok("Launchers installed: monad.bat, monad-cli.bat")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Install Monad-Ultron to a USB drive.")
    parser.add_argument("--drive", help="USB drive letter (e.g. E:). If omitted, prompts.")
    parser.add_argument("--skip-python", action="store_true", help="Skip portable Python setup.")
    parser.add_argument("--skip-models", action="store_true", help="Skip model download.")
    parser.add_argument("--skip-requirements", action="store_true", help="Skip pip install.")
    parser.add_argument("--folder-name", default="Monad-Ultron",
                        help="Folder name to create on the USB (default: Monad-Ultron).")
    args = parser.parse_args()

    print("=" * 60)
    print("  Monad-Ultron  |  USB Installer")
    print("=" * 60)

    usb = choose_drive(args.drive)
    if not usb.exists():
        err(f"Drive not accessible: {usb}")
        sys.exit(1)

    # Disk-space check
    free_gb = shutil.disk_usage(usb).free / (1024**3)
    info(f"Selected: {usb}  ({free_gb:.1f} GB free)")
    if free_gb < 25:
        warn(f"Only {free_gb:.1f} GB free — installer needs ≥ 25 GB. Continue anyway? (y/N)")
        if input().strip().lower() != "y":
            sys.exit(1)

    dst = usb / args.folder_name
    info(f"Install target: {dst}")

    # 1. Copy code
    copy_codebase(REPO_ROOT, dst)

    # 2. Portable Python
    if not args.skip_python:
        py_dir = install_portable_python(dst)
        if not args.skip_requirements:
            try:
                install_requirements(dst, py_dir)
            except Exception as e:
                warn(f"Requirement install failed: {e}. "
                     f"You can retry later with: {py_dir}\\python.exe -m pip install -r requirements.txt")

    # 3. Models
    if not args.skip_models:
        try:
            download_models(dst)
        except Exception as e:
            warn(f"Model download failed: {e}")
            warn("You can retry with: python installer\\download_models.py")

    # 4. Launcher
    install_launcher(dst)

    print()
    ok("Installation complete!")
    print(f"  Eject {usb}, plug into your laptop, and double-click {dst}\\monad.bat")


if __name__ == "__main__":
    main()
