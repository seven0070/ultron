@echo off
REM Reference launcher — the actual USB launcher is written by installer/install_to_usb.py
REM at the USB root. This copy is here in the repo for reference only.
setlocal
cd /d "%~dp0.."
python run.py %*
endlocal
