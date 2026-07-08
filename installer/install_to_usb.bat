@echo off
REM ============================================================================
REM Monad-Ultron — ONE-CLICK USB Installer
REM
REM What this does:
REM   1. Checks that Python 3.12+ is installed on your desktop
REM   2. Launches the interactive install wizard
REM   3. Wizard finds your USB, asks which profile, downloads everything
REM
REM Just double-click this file.
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0.."
set MONAD_SRC=%CD%

REM Enable UTF-8 for the pretty progress bars
chcp 65001 >nul 2>&1

echo.
echo  ================================================================
echo    Monad-Ultron  ^|  One-Click USB Installer
echo  ================================================================
echo.

REM --- Python check on the DESKTOP (used only to bootstrap) --------------------
where python >nul 2>&1
if errorlevel 1 (
    echo   [X] Python is not installed on this desktop.
    echo.
    echo   Install Python 3.12+ from https://python.org/downloads
    echo   Make sure to check "Add Python to PATH" during install.
    echo.
    echo   Then re-run this installer.
    pause
    exit /b 1
)

REM --- Version check ----------------------------------------------------------
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo   Python %PYVER% detected on desktop.
echo.

REM --- Ensure PyYAML is installed for the wizard (silent) ---------------------
python -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo   Installing PyYAML for the installer...
    python -m pip install --quiet pyyaml >nul 2>&1
)

REM --- Launch the wizard ------------------------------------------------------
python "%MONAD_SRC%\installer\install_wizard.py" %*
set EXITCODE=%errorlevel%

if not %EXITCODE% == 0 (
    echo.
    echo   [!] Installer exited with code %EXITCODE%
    pause
    exit /b %EXITCODE%
)

echo.
echo   Press any key to close this window.
pause >nul
endlocal
