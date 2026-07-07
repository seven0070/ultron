@echo off
REM ============================================================================
REM Monad-Ultron — One-click USB installer
REM
REM Run this on your DESKTOP (Windows 11) with a 128 GB USB drive plugged in.
REM It will:
REM   1. Ask you to pick your USB drive letter
REM   2. Copy the Monad codebase to it
REM   3. Download portable Python 3.12 to the USB
REM   4. Create a venv on the USB and install requirements
REM   5. Download the 3 GGUF models (~15 GB) to USB\models\
REM   6. Drop a launcher (monad.bat) at the USB root
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0.."
set MONAD_SRC=%CD%

echo.
echo  ============================================================
echo   Monad-Ultron  ^|  USB Installer
echo  ============================================================
echo.
echo   Source: %MONAD_SRC%
echo.

REM --- Detect Python on the desktop (needed only to run the installer script) --
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed on this desktop.
    echo         Install Python 3.12+ from https://python.org first, then re-run.
    pause
    exit /b 1
)

REM --- Run the Python installer -----------------------------------------------
python "%MONAD_SRC%\installer\install_to_usb.py" %*
if errorlevel 1 (
    echo.
    echo [ERROR] Installer failed. Scroll up to see what went wrong.
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   ^  Install complete!
echo  ============================================================
echo   Eject the USB drive, plug it into your laptop,
echo   and double-click ^"monad.bat^" at the USB root.
echo  ============================================================
echo.
pause
endlocal
