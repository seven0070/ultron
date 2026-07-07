@echo off
REM Reference CLI launcher — installer writes the real one at the USB root.
setlocal
cd /d "%~dp0.."
python -m monad.ui.cli %*
endlocal
