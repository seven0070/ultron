#!/usr/bin/env bash
# =========================================================================
#  Monad-Ultron — one-click Web App launcher (Linux/macOS)
# =========================================================================
set -e
cd "$(dirname "$0")/.."
REPO="$(pwd)"

echo "=================================================="
echo "  Monad-Ultron Web App"
echo "=================================================="

# --- Python backend ------------------------------------------------------
if ! command -v python >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
    echo "[ERROR] Python 3.12+ not found. Install first."
    exit 1
fi
PY=$(command -v python3 || command -v python)

echo "Starting Monad backend on http://127.0.0.1:8765 …"
"$PY" -m monad.ui.cli serve --host 127.0.0.1 --port 8765 &
BACKEND=$!

# --- Node frontend -------------------------------------------------------
if ! command -v npm >/dev/null 2>&1; then
    echo "[WARN] Node.js not found. Only the FastAPI dashboard at :8765 will work."
    echo "       Install Node 20+ from https://nodejs.org for the polished web UI."
    wait $BACKEND
    exit 0
fi

if [ ! -d "webapp/node_modules" ]; then
    echo "First run — installing web app dependencies (~1 minute)…"
    (cd webapp && npm install)
fi

echo "Starting web app on http://127.0.0.1:3000 …"
(cd webapp && npm run dev) &
FRONTEND=$!

sleep 4
if command -v xdg-open >/dev/null; then xdg-open http://127.0.0.1:3000 & fi
if command -v open >/dev/null;      then open     http://127.0.0.1:3000 & fi

echo ""
echo "Both servers running."
echo "  Backend  : http://127.0.0.1:8765"
echo "  Web app  : http://127.0.0.1:3000"
echo "Press Ctrl-C to stop both."

trap "kill $BACKEND $FRONTEND 2>/dev/null; exit 0" INT TERM
wait
