@echo off
REM =======================================================================
REM  Monad-Ultron — one-click Web App launcher (Windows)
REM  Starts the Python backend AND the Next.js frontend in separate windows,
REM  then opens your browser to the landing page.
REM =======================================================================
setlocal
cd /d "%~dp0.."
set REPO=%CD%

echo.
echo  ==================================================
echo   Monad-Ultron Web App
echo  ==================================================
echo.

REM --- Backend (FastAPI) ---
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not on PATH. Install Python 3.12+ or run this from the USB
    echo         (the USB installer sets up portable Python for you).
    pause & exit /b 1
)

echo Starting Monad backend on http://127.0.0.1:8765 ...
start "Monad Backend" cmd /k "cd /d %REPO% && python -m monad.ui.cli serve --host 127.0.0.1 --port 8765"

REM --- Frontend (Next.js) ---
where npm >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARN] Node.js not found. The landing page will not start until you install Node 20+.
    echo         Backend REST API and dashboard at http://127.0.0.1:8765 will still work.
    echo         Install: https://nodejs.org
    pause & exit /b 0
)

if not exist "webapp\node_modules" (
    echo First run detected. Installing web app dependencies (one-time, ~1 minute)...
    pushd webapp
    call npm install
    popd
)

echo Starting web app on http://127.0.0.1:3000 ...
start "Monad Web App" cmd /k "cd /d %REPO%\webapp && npm run dev"

REM Give both a moment, then open the browser
timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:3000"

echo.
echo  Opened http://127.0.0.1:3000 in your browser.
echo  Close the two other windows to shut Monad down.
echo.
endlocal
