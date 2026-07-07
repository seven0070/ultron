#!/usr/bin/env bash
# ============================================================================
#  Monad-Ultron — one-shot GitHub push script
# ============================================================================
#  Usage:
#    ./scripts/push_to_github.sh <your-github-username> [repo-name]
#
#  What it does:
#    1. Replaces every "YOUR_USERNAME" placeholder with your actual username
#    2. Commits the personalization
#    3. Sets up the git remote
#    4. Pushes main + all tags to GitHub
#
#  Prerequisites (do these FIRST):
#    A. Create an empty repo on GitHub:
#         https://github.com/new
#         Name: Monad-Ultron (or whatever you pass as arg 2)
#         Do NOT initialize with README / .gitignore / LICENSE (we have them)
#    B. Have GitHub auth ready. Either:
#         - GitHub CLI: `gh auth login` (easiest)
#         - HTTPS: personal access token when git prompts
#         - SSH: your ssh key registered with GitHub
# ============================================================================

set -e

USERNAME="${1:?Usage: $0 <github-username> [repo-name]}"
REPO="${2:-Monad-Ultron}"

# Move to repo root regardless of where the script was invoked from
cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

echo "============================================================"
echo "  Monad-Ultron → GitHub"
echo "============================================================"
echo "  Username:  $USERNAME"
echo "  Repo:      $REPO"
echo "  Root:      $REPO_ROOT"
echo "============================================================"

# ---------------------------------------------------------------------------
# Step 1 — sanity checks
# ---------------------------------------------------------------------------

if [ ! -d ".git" ]; then
  echo "[X] not a git repo. Aborting."
  exit 1
fi

CLEAN=$(git status --porcelain)
if [ -n "$CLEAN" ]; then
  echo "[!] working tree has uncommitted changes:"
  echo "$CLEAN"
  read -p "    Continue anyway? [y/N] " ans
  [ "$ans" = "y" ] || [ "$ans" = "Y" ] || exit 1
fi

# ---------------------------------------------------------------------------
# Step 2 — find/replace YOUR_USERNAME
# ---------------------------------------------------------------------------

echo ""
echo "[1/4] Replacing YOUR_USERNAME → $USERNAME …"

# Files we know contain the placeholder — grep the repo to be safe
FILES=$(grep -rl "YOUR_USERNAME" . \
        --exclude-dir=.git \
        --exclude-dir=.venv \
        --exclude-dir=__pycache__ \
        --exclude-dir=node_modules \
        --exclude-dir=models \
        --exclude-dir=memory_data \
        --exclude-dir=python_portable \
        --exclude=push_to_github.sh 2>/dev/null || true)

if [ -z "$FILES" ]; then
  echo "      (no YOUR_USERNAME placeholders found — already personalized?)"
else
  echo "$FILES" | while read -r f; do
    # Portable in-place sed (BSD + GNU)
    if sed --version >/dev/null 2>&1; then
      sed -i "s|YOUR_USERNAME|$USERNAME|g" "$f"           # GNU
    else
      sed -i "" "s|YOUR_USERNAME|$USERNAME|g" "$f"        # BSD (macOS)
    fi
    echo "      · $f"
  done
fi

# ---------------------------------------------------------------------------
# Step 3 — commit the personalization
# ---------------------------------------------------------------------------

echo ""
echo "[2/4] Committing personalization …"

if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -q -m "Personalize repo URLs for $USERNAME/$REPO"
  echo "      committed."
else
  echo "      nothing to commit."
fi

# ---------------------------------------------------------------------------
# Step 4 — set remote (idempotent)
# ---------------------------------------------------------------------------

echo ""
echo "[3/4] Configuring 'origin' remote …"

REMOTE_URL="https://github.com/$USERNAME/$REPO.git"

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL"
  echo "      updated to $REMOTE_URL"
else
  git remote add origin "$REMOTE_URL"
  echo "      added $REMOTE_URL"
fi

# Ensure we're on main
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "      renaming '$CURRENT_BRANCH' → 'main'"
  git branch -M main
fi

# ---------------------------------------------------------------------------
# Step 5 — push
# ---------------------------------------------------------------------------

echo ""
echo "[4/4] Pushing to GitHub …"
echo "      (if this hangs, you may need to authenticate: gh auth login, or"
echo "       use a personal access token when prompted for password)"
echo ""

git push -u origin main
git push origin --tags

echo ""
echo "============================================================"
echo "  ✔ pushed!"
echo "============================================================"
echo "  Repo:      https://github.com/$USERNAME/$REPO"
echo "  Actions:   https://github.com/$USERNAME/$REPO/actions"
echo "  Releases:  https://github.com/$USERNAME/$REPO/releases"
echo "============================================================"
