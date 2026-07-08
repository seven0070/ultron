#!/usr/bin/env bash
# ============================================================================
#  Monad-Ultron — One-Click USB Installer (Linux/macOS)
# ============================================================================
set -e
cd "$(dirname "$0")/.."
REPO="$(pwd)"

echo ""
echo " ================================================================"
echo "   Monad-Ultron  |  One-Click USB Installer"
echo " ================================================================"
echo ""

# --- Python check -----------------------------------------------------------
if ! command -v python3 >/dev/null 2>&1 && ! command -v python >/dev/null 2>&1; then
    echo "  [X] Python not found. Install Python 3.12+ first."
    exit 1
fi
PY=$(command -v python3 || command -v python)
echo "  $($PY --version) detected."
echo ""

# Ensure pyyaml
if ! "$PY" -c "import yaml" >/dev/null 2>&1; then
    echo "  Installing PyYAML for the installer…"
    "$PY" -m pip install --quiet pyyaml >/dev/null 2>&1 || true
fi

# --- Launch wizard ----------------------------------------------------------
"$PY" "$REPO/installer/install_wizard.py" "$@"
