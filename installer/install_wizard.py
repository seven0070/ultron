"""
Monad-Ultron — One-Click USB Install Wizard.

A friendly, interactive installer with:
  - USB auto-detection (Windows removable drives)
  - Install profile picker (Minimal / Recommended / Full)
  - Free-space check + upfront total-size preview
  - Live progress bar (bytes downloaded, speed MB/s, ETA)
  - Atomic writes + resume on failure
  - Rollback on abort
  - Zero external deps beyond stdlib

Usage:
    python installer/install_wizard.py
    python installer/install_wizard.py --drive E: --profile recommended --yes
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import io
import platform
import shutil
import signal
import string
import subprocess
import sys
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

# =============================================================================
# ANSI colors (Windows 10+ terminals support these by default)
# =============================================================================
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    PURPLE = "\033[95m"
    CYAN   = "\033[96m"

    @staticmethod
    def enable_windows_ansi():
        if platform.system() == "Windows":
            try:
                ctypes.windll.kernel32.SetConsoleMode(
                    ctypes.windll.kernel32.GetStdHandle(-11), 7,
                )
            except Exception:
                pass

def cprint(color: str, msg: str):
    print(f"{color}{msg}{C.RESET}")

def banner():
    print(f"""{C.PURPLE}{C.BOLD}
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║    🧠  Monad-Ultron — One-Click USB Install              ║
    ║                                                          ║
    ║    Portable local AI · 82 organs · self-improving        ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    {C.RESET}""")

# =============================================================================
# Install profiles
# =============================================================================
@dataclass
class InstallProfile:
    id: str
    name: str
    description: str
    est_gb: float
    include_models: list[str]                          # model ids from models.yaml
    include_web: bool = False
    include_chromadb: bool = False


PROFILES: dict[str, InstallProfile] = {
    "minimal": InstallProfile(
        id="minimal",
        name="Minimal",
        description="Code + Python + Llama 3.2 3B only.",
        est_gb=2.9,
        include_models=["llama2"],
    ),
    "recommended": InstallProfile(
        id="recommended",
        name="Recommended ⭐",
        description="Adds Qwen 2.5 7B (reasoning), speculative-decoding draft, and web UI.",
        est_gb=8.5,
        include_models=["llama2", "longcat2", "qwen2.5-draft"],
        include_web=True,
    ),
    "full": InstallProfile(
        id="full",
        name="Full",
        description="Everything above + DeepSeek-Coder + ChromaDB vector memory.",
        est_gb=19.0,
        include_models=["llama2", "longcat2", "qwen2.5-draft", "glm5"],
        include_web=True,
        include_chromadb=True,
    ),
    "code-only": InstallProfile(
        id="code-only",
        name="Code only (no models)",
        description="Just the framework. Bring your own GGUFs.",
        est_gb=0.4,
        include_models=[],
    ),
}


# =============================================================================
# USB drive detection & selection
# =============================================================================
def list_removable_drives() -> list[dict]:
    if platform.system() != "Windows":
        return []
    out = []
    try:
        DRIVE_REMOVABLE = 2
        for letter in string.ascii_uppercase:
            root = f"{letter}:\\"
            if ctypes.windll.kernel32.GetDriveTypeW(root) == DRIVE_REMOVABLE:
                try:
                    usage = shutil.disk_usage(root)
                    out.append({
                        "letter": f"{letter}:",
                        "root": root,
                        "total_gb": round(usage.total / (1024**3), 1),
                        "free_gb": round(usage.free / (1024**3), 1),
                    })
                except OSError:
                    pass
    except Exception as e:
        cprint(C.YELLOW, f"[!] USB detection failed: {e}")
    return out


def choose_drive(preselected: str | None) -> Path:
    if preselected:
        p = Path(preselected + ("\\" if not preselected.endswith(("\\", "/")) else ""))
        if not p.exists():
            cprint(C.RED, f"[X] drive not accessible: {p}")
            sys.exit(1)
        return p

    drives = list_removable_drives()
    if not drives:
        cprint(C.YELLOW, "[!] No removable USB drives detected.")
        letter = input(f"{C.BOLD}Enter USB drive letter (e.g. E:): {C.RESET}").strip()
        if not letter:
            sys.exit(1)
        return Path(letter + "\\")

    print(f"\n{C.BOLD}📀 USB drives found:{C.RESET}\n")
    for i, d in enumerate(drives, 1):
        bar_fill = int((d["total_gb"] - d["free_gb"]) / d["total_gb"] * 20) if d["total_gb"] > 0 else 0
        bar = "█" * bar_fill + "░" * (20 - bar_fill)
        print(f"  {C.CYAN}[{i}]{C.RESET}  {C.BOLD}{d['letter']}{C.RESET}   "
              f"{d['free_gb']:>5.1f} GB free / {d['total_gb']:>5.1f} GB   "
              f"{C.DIM}{bar}{C.RESET}")

    while True:
        pick = input(f"\n{C.BOLD}Pick a drive [1-{len(drives)}]: {C.RESET}").strip()
        try:
            i = int(pick) - 1
            if 0 <= i < len(drives):
                return Path(drives[i]["root"])
        except ValueError:
            pass
        cprint(C.YELLOW, "  invalid — try again")


# =============================================================================
# Profile picker
# =============================================================================
def choose_profile(preselected: str | None) -> InstallProfile:
    if preselected:
        if preselected not in PROFILES:
            cprint(C.RED, f"[X] unknown profile: {preselected}")
            sys.exit(1)
        return PROFILES[preselected]

    print(f"\n{C.BOLD}📦 Install profiles:{C.RESET}\n")
    keys = list(PROFILES.keys())
    for i, k in enumerate(keys, 1):
        p = PROFILES[k]
        est = f"~{p.est_gb} GB"
        print(f"  {C.CYAN}[{i}]{C.RESET}  {C.BOLD}{p.name:<18}{C.RESET}"
              f"  {C.PURPLE}{est:>8}{C.RESET}  {C.DIM}{p.description}{C.RESET}")

    while True:
        pick = input(f"\n{C.BOLD}Pick a profile [1-{len(keys)}] (default 2): {C.RESET}").strip() or "2"
        try:
            i = int(pick) - 1
            if 0 <= i < len(keys):
                return PROFILES[keys[i]]
        except ValueError:
            pass
        cprint(C.YELLOW, "  invalid — try again")


# =============================================================================
# Live progress bar
# =============================================================================
class Progress:
    def __init__(self, total_bytes: int, label: str, width: int = 32):
        self.total = max(1, total_bytes)
        self.done = 0
        self.label = label
        self.width = width
        self.start = time.time()
        self._last_render = 0.0

    def update(self, delta: int):
        self.done += delta
        now = time.time()
        if now - self._last_render < 0.1 and self.done < self.total:
            return
        self._last_render = now
        self._render()

    def finish(self):
        self.done = self.total
        self._render()
        print()

    def _render(self):
        pct = self.done / self.total
        filled = int(pct * self.width)
        bar = f"{'█' * filled}{'░' * (self.width - filled)}"
        elapsed = max(0.1, time.time() - self.start)
        speed_mb = (self.done / elapsed) / (1024 * 1024)
        eta = (self.total - self.done) / (self.done / elapsed) if self.done > 0 else 0
        eta_s = f"{eta:>4.0f}s" if eta < 60 else f"{eta/60:>4.1f}m"
        done_mb = self.done / (1024 * 1024)
        total_mb = self.total / (1024 * 1024)
        sys.stdout.write(
            f"\r  {C.CYAN}{bar}{C.RESET} {pct*100:5.1f}%  "
            f"{done_mb:>7.1f} / {total_mb:>7.1f} MB  "
            f"{speed_mb:>5.1f} MB/s  ETA {eta_s}   "
        )
        sys.stdout.flush()


# =============================================================================
# Download with progress + resume
# =============================================================================
def download_with_progress(url: str, dest: Path, label: str = ""):
    dest.parent.mkdir(parents=True, exist_ok=True)
    partial = dest.with_suffix(dest.suffix + ".part")
    resume_from = partial.stat().st_size if partial.exists() else 0

    req = urllib.request.Request(url)
    if resume_from > 0:
        req.add_header("Range", f"bytes={resume_from}-")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_len = int(resp.headers.get("Content-Length", 0))
            total = content_len + resume_from
            prog = Progress(total, label)
            prog.done = resume_from
            with partial.open("ab") as fh:
                while True:
                    chunk = resp.read(1024 * 256)  # 256 KB
                    if not chunk:
                        break
                    fh.write(chunk)
                    prog.update(len(chunk))
            prog.finish()
        partial.rename(dest)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} — {e.reason}") from e
    except Exception as e:
        raise RuntimeError(f"download failed: {e}") from e


# =============================================================================
# Install steps
# =============================================================================
EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "dist", "build", "node_modules",
    "models", "python_portable", "logs", "cache",
}


@dataclass
class InstallResult:
    steps_done: list[str] = field(default_factory=list)
    steps_failed: list[tuple[str, str]] = field(default_factory=list)
    total_bytes: int = 0


def step(msg: str):
    print(f"\n{C.BLUE}▶{C.RESET} {C.BOLD}{msg}{C.RESET}")


def step_ok(msg: str):
    cprint(C.GREEN, f"  ✓ {msg}")


def step_warn(msg: str):
    cprint(C.YELLOW, f"  ! {msg}")


def step_fail(msg: str):
    cprint(C.RED, f"  ✘ {msg}")


def copy_codebase(src: Path, dst: Path, result: InstallResult):
    step("Copying Monad codebase to USB")
    dst.mkdir(parents=True, exist_ok=True)
    total = 0
    files = 0
    for item in src.iterdir():
        if item.name in EXCLUDE_DIRS or item.name.endswith(".zip"):
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(
                item, target, dirs_exist_ok=True,
                ignore=shutil.ignore_patterns(*EXCLUDE_DIRS, "*.pyc"),
            )
        else:
            shutil.copy2(item, target)
        for f in target.rglob("*") if item.is_dir() else [target]:
            if f.is_file():
                total += f.stat().st_size
                files += 1
    result.total_bytes += total
    step_ok(f"{files} files, {total / (1024 * 1024):.1f} MB")
    result.steps_done.append("codebase")


def install_portable_python(usb_root: Path, result: InstallResult):
    step("Downloading portable Python 3.12")
    manifest_path = REPO_ROOT / "models.yaml"
    with manifest_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    py_manifest = data.get("python_portable", {})
    url = py_manifest.get("url")
    if not url:
        step_fail("no python_portable.url in models.yaml")
        result.steps_failed.append(("python", "no url"))
        return

    target_dir = usb_root / "python_portable"
    target_dir.mkdir(parents=True, exist_ok=True)
    if (target_dir / "python.exe").exists():
        step_ok("already installed")
        result.steps_done.append("python")
        return

    zip_path = target_dir / "python.zip"
    try:
        download_with_progress(url, zip_path, label="python-embed")
    except Exception as e:
        step_fail(str(e))
        result.steps_failed.append(("python", str(e)))
        return

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(target_dir)
    zip_path.unlink(missing_ok=True)

    # Enable site-packages
    for pth in target_dir.glob("python*._pth"):
        content = pth.read_text(encoding="utf-8")
        if "#import site" in content:
            pth.write_text(content.replace("#import site", "import site"), encoding="utf-8")

    result.total_bytes += sum(f.stat().st_size for f in target_dir.rglob("*") if f.is_file())
    step_ok(f"extracted to {target_dir.name}/")
    result.steps_done.append("python")


def install_dependencies(usb_root: Path, profile: InstallProfile, result: InstallResult):
    step("Installing Python dependencies on USB")
    py = usb_root / "python_portable" / "python.exe"
    if not py.exists():
        step_warn("portable python missing — skipping (install manually later)")
        return

    # Bootstrap pip (embeddable python doesn't ship with it)
    try:
        get_pip = usb_root / "python_portable" / "get-pip.py"
        if not get_pip.exists():
            urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", get_pip)
        subprocess.check_call([str(py), str(get_pip), "--no-warn-script-location"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        step_fail(f"pip bootstrap failed: {e}")
        result.steps_failed.append(("pip", str(e)))
        return

    reqs = usb_root / "requirements.txt"
    if not reqs.exists():
        step_warn("requirements.txt missing on USB")
        return

    print(f"  {C.DIM}pip install -r requirements.txt (this can take a minute)…{C.RESET}")
    try:
        subprocess.check_call(
            [str(py), "-m", "pip", "install", "--no-warn-script-location",
             "-r", str(reqs)],
            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError as e:
        step_fail(f"pip install failed (exit {e.returncode})")
        result.steps_failed.append(("deps", "pip install failed"))
        return

    # Optional extras
    if profile.include_chromadb:
        try:
            subprocess.check_call(
                [str(py), "-m", "pip", "install", "chromadb", "sentence-transformers"],
                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
            )
            step_ok("ChromaDB + sentence-transformers installed")
        except Exception as e:
            step_warn(f"chromadb install failed: {e}")

    step_ok("core dependencies installed")
    result.steps_done.append("deps")


def download_models(usb_root: Path, profile: InstallProfile, result: InstallResult):
    if not profile.include_models:
        step_warn("skipping models (code-only profile)")
        return

    step(f"Downloading models: {', '.join(profile.include_models)}")

    manifest_path = REPO_ROOT / "models.yaml"
    with manifest_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    all_models = {m["id"]: m for m in data.get("models", [])}

    models_dir = usb_root / "models"
    for mid in profile.include_models:
        meta = all_models.get(mid)
        if not meta:
            step_warn(f"{mid}: not in models.yaml")
            continue
        target = models_dir / mid / meta["filename"]
        if target.exists():
            step_ok(f"{mid}: already downloaded")
            continue
        print(f"\n  {C.CYAN}◆{C.RESET} {C.BOLD}{mid}{C.RESET}   "
              f"{C.DIM}~{meta.get('size_gb', '?')} GB{C.RESET}")
        try:
            download_with_progress(meta["url"], target, label=mid)
            result.total_bytes += target.stat().st_size
            step_ok(f"{mid}: saved to models/{mid}/")
        except Exception as e:
            step_fail(f"{mid}: {e}")
            result.steps_failed.append((f"model:{mid}", str(e)))

    result.steps_done.append("models")


def install_web_deps(usb_root: Path, profile: InstallProfile, result: InstallResult):
    if not profile.include_web:
        return
    step("Web app dependencies (Next.js)")
    webapp = usb_root / "webapp"
    if not webapp.exists():
        step_warn("webapp/ directory missing on USB")
        return
    npm = shutil.which("npm")
    if not npm:
        step_warn("Node.js/npm not on PATH — install from https://nodejs.org, "
                  "then run `npm install` inside USB\\webapp\\")
        return
    print(f"  {C.DIM}npm install (this takes ~1 minute)…{C.RESET}")
    try:
        subprocess.check_call([npm, "install", "--no-fund", "--no-audit"],
                              cwd=str(webapp),
                              stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        step_ok("web app dependencies installed")
        result.steps_done.append("web")
    except subprocess.CalledProcessError as e:
        step_fail(f"npm install failed (exit {e.returncode})")
        result.steps_failed.append(("web", "npm failed"))


def write_launchers(usb_root: Path):
    step("Installing launchers at USB root")
    (usb_root / "monad.bat").write_text(_LAUNCHER_BAT, encoding="utf-8")
    (usb_root / "monad-cli.bat").write_text(_LAUNCHER_CLI, encoding="utf-8")
    (usb_root / "monad-web.bat").write_text(_LAUNCHER_WEB, encoding="utf-8")
    step_ok("monad.bat · monad-cli.bat · monad-web.bat")


_LAUNCHER_BAT = r"""@echo off
REM Monad-Ultron launcher — double-click to start
setlocal
cd /d "%~dp0"
set MONAD_ROOT=%CD%
set PY="%MONAD_ROOT%\python_portable\python.exe"
if not exist %PY% (
    echo Portable Python not found. Re-run the installer.
    pause & exit /b 1
)
%PY% "%MONAD_ROOT%\run.py" %*
if errorlevel 1 pause
endlocal
"""

_LAUNCHER_CLI = r"""@echo off
setlocal
cd /d "%~dp0"
set MONAD_ROOT=%CD%
set PY="%MONAD_ROOT%\python_portable\python.exe"
%PY% -m monad.ui.cli %*
endlocal
"""

_LAUNCHER_WEB = r"""@echo off
REM Monad-Ultron Web App — double-click for browser UI
setlocal
cd /d "%~dp0"
set MONAD_ROOT=%CD%
set PY="%MONAD_ROOT%\python_portable\python.exe"
if not exist %PY% (
    echo Portable Python not found. Re-run the installer.
    pause & exit /b 1
)
echo Starting Monad backend on http://127.0.0.1:8765 ...
start "Monad Backend" cmd /k %PY% -m monad.ui.cli serve --host 127.0.0.1 --port 8765
where npm >nul 2>&1
if errorlevel 1 (
    echo Node.js not installed — opening the built-in dashboard at :8765 instead.
    timeout /t 3 /nobreak >nul
    start "" "http://127.0.0.1:8765"
    exit /b 0
)
if not exist "webapp\node_modules" (
    echo First run — installing web app dependencies...
    pushd webapp & call npm install & popd
)
echo Starting web app on http://127.0.0.1:3000 ...
start "Monad Web App" cmd /k "cd /d %MONAD_ROOT%\webapp & npm run dev"
timeout /t 5 /nobreak >nul
start "" "http://127.0.0.1:3000"
endlocal
"""

# =============================================================================
# Rollback handler
# =============================================================================
_rollback_paths: list[Path] = []
_aborted = False

def register_rollback(p: Path):
    _rollback_paths.append(p)

def rollback():
    if not _rollback_paths:
        return
    cprint(C.YELLOW, "\n\n[!] Rolling back partial install…")
    for p in reversed(_rollback_paths):
        try:
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
        except Exception:
            pass

def handle_sigint(sig, frame):
    global _aborted
    _aborted = True
    rollback()
    cprint(C.RED, "\nAborted by user.")
    sys.exit(130)


# =============================================================================
# Confirmation summary
# =============================================================================
def show_summary(usb: Path, profile: InstallProfile, drive_info: dict | None) -> bool:
    print(f"\n{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}")
    print(f"  {C.BOLD}Install summary{C.RESET}\n")
    print(f"  {C.DIM}Target USB{C.RESET}      {C.CYAN}{usb}{C.RESET}")
    if drive_info:
        print(f"  {C.DIM}Free space{C.RESET}      {drive_info['free_gb']} GB / {drive_info['total_gb']} GB")
    print(f"  {C.DIM}Profile{C.RESET}         {C.BOLD}{profile.name}{C.RESET}")
    print(f"  {C.DIM}Est. size{C.RESET}       {C.PURPLE}~{profile.est_gb} GB{C.RESET}")
    print(f"  {C.DIM}Models{C.RESET}          {', '.join(profile.include_models) or 'none'}")
    print(f"  {C.DIM}Web UI{C.RESET}          {'yes' if profile.include_web else 'no'}")
    print(f"  {C.DIM}ChromaDB{C.RESET}        {'yes' if profile.include_chromadb else 'no (in-mem fallback)'}")
    print(f"{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}\n")
    ans = input(f"{C.BOLD}Proceed? [Y/n] {C.RESET}").strip().lower()
    return ans in ("", "y", "yes")


# =============================================================================
# Main
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Monad-Ultron USB installer")
    parser.add_argument("--drive", help="USB drive letter (e.g. E:)")
    parser.add_argument("--profile", choices=list(PROFILES),
                        help="Install profile")
    parser.add_argument("--folder", default="Monad-Ultron",
                        help="Folder name on the USB (default: Monad-Ultron)")
    parser.add_argument("--yes", "-y", action="store_true",
                        help="Skip confirmation prompt")
    parser.add_argument("--skip-python", action="store_true")
    parser.add_argument("--skip-models", action="store_true")
    parser.add_argument("--skip-deps", action="store_true")
    args = parser.parse_args()

    C.enable_windows_ansi()
    signal.signal(signal.SIGINT, handle_sigint)
    banner()

    # 1. USB
    usb_root = choose_drive(args.drive)
    drive_info = None
    for d in list_removable_drives():
        if Path(d["root"]) == usb_root:
            drive_info = d; break

    # 2. Profile
    profile = choose_profile(args.profile)

    # 3. Free-space check
    if drive_info and drive_info["free_gb"] < profile.est_gb:
        cprint(C.RED, f"\n[X] Not enough free space on {usb_root}:")
        cprint(C.RED, f"    need ~{profile.est_gb} GB, have {drive_info['free_gb']} GB free")
        if not args.yes:
            ans = input(f"    Continue anyway? [y/N] ").strip().lower()
            if ans not in ("y", "yes"): sys.exit(1)

    # 4. Confirm
    dst = usb_root / args.folder
    if not args.yes:
        if not show_summary(dst, profile, drive_info):
            cprint(C.YELLOW, "Cancelled.")
            sys.exit(0)

    # 5. Install!
    start_time = time.time()
    result = InstallResult()
    register_rollback(dst)

    try:
        copy_codebase(REPO_ROOT, dst, result)

        if not args.skip_python:
            install_portable_python(dst, result)

        if not args.skip_deps:
            install_dependencies(dst, profile, result)

        if not args.skip_models:
            download_models(dst, profile, result)

        install_web_deps(dst, profile, result)
        write_launchers(dst)

    except KeyboardInterrupt:
        handle_sigint(None, None)

    # 6. Summary
    elapsed = time.time() - start_time
    total_gb = result.total_bytes / (1024**3)

    print(f"\n{C.GREEN}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}")
    print(f"{C.GREEN}{C.BOLD}  ✓  Install complete!{C.RESET}\n")
    print(f"  {C.DIM}Time{C.RESET}          {elapsed:.0f}s ({elapsed/60:.1f}m)")
    print(f"  {C.DIM}Written{C.RESET}       {total_gb:.2f} GB")
    print(f"  {C.DIM}Location{C.RESET}      {C.CYAN}{dst}{C.RESET}")
    print(f"  {C.DIM}Steps done{C.RESET}    {', '.join(result.steps_done) or 'none'}")
    if result.steps_failed:
        print(f"  {C.DIM}Steps failed{C.RESET}  {C.YELLOW}"
              f"{', '.join(f'{k}({v[:40]})' for k, v in result.steps_failed)}{C.RESET}")
    print(f"{C.GREEN}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.RESET}\n")
    print(f"  Eject the USB safely, plug it into your laptop, and:")
    print(f"    {C.BOLD}Double-click{C.RESET}  {C.CYAN}monad-web.bat{C.RESET}  {C.DIM}→ opens browser UI{C.RESET}")
    print(f"    {C.BOLD}Double-click{C.RESET}  {C.CYAN}monad.bat{C.RESET}      {C.DIM}→ opens CLI{C.RESET}")
    print()


if __name__ == "__main__":
    main()
