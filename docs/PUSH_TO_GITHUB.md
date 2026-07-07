# Push Monad-Ultron to GitHub

Three ways, pick one.

---

## 🚀 Option A — One-shot script (recommended)

**Step 1 — Create the empty repo on GitHub**

Go to https://github.com/new and create a repo named `Monad-Ultron` (or whatever you like).

⚠️ **Do NOT initialize** with a README, .gitignore, or LICENSE. We already have all three and GitHub will refuse the push if it has its own initial commit.

**Step 2 — Run the script**

Linux / macOS / Git-Bash on Windows:
```bash
cd Monad-Ultron
chmod +x scripts/push_to_github.sh
./scripts/push_to_github.sh your-github-username
# or with a custom repo name:
./scripts/push_to_github.sh your-github-username My-Monad-Fork
```

Windows PowerShell:
```powershell
cd Monad-Ultron
.\scripts\push_to_github.ps1 -Username your-github-username
# or:
.\scripts\push_to_github.ps1 -Username your-github-username -Repo My-Monad-Fork
```

The script will:
1. Replace every `YOUR_USERNAME` placeholder in README, pyproject.toml, docs, etc.
2. Commit that change
3. Add the `origin` remote (or update it)
4. Push `main` + all 7 tags (v0.1.0 → v0.7.0)

---

## 🔧 Option B — Manual 4 commands

```bash
cd Monad-Ultron

# 1. Personalize URLs (one grep-replace)
find . -type f \( -name "*.md" -o -name "*.toml" -o -name "*.py" -o -name "*.yaml" \) \
     -not -path "./.git/*" \
     -exec sed -i "s|YOUR_USERNAME|your-github-username|g" {} +
git add -A && git commit -m "Personalize URLs"

# 2. Add remote
git remote add origin https://github.com/your-github-username/Monad-Ultron.git
git branch -M main

# 3. Push everything
git push -u origin main
git push origin --tags
```

---

## 🌐 Option C — GitHub CLI (if you have `gh` installed)

```bash
cd Monad-Ultron

# Auth once if you haven't
gh auth login

# Create + push in one shot (public repo, current dir source)
gh repo create Monad-Ultron --source=. --public --push

# Then push tags separately
git push origin --tags
```

For a private repo, swap `--public` → `--private`.

---

## 🔐 Auth options

The push step needs auth. In order of ease:

1. **GitHub CLI** (`gh auth login`) — one-time setup, works everywhere
2. **Personal access token** — go to https://github.com/settings/tokens, create a fine-grained token with `Contents: read/write`, paste it as password when git prompts
3. **SSH key** — set `git remote set-url origin git@github.com:USERNAME/Monad-Ultron.git`

---

## 📋 After the push

Your repo will have:

- ✅ Full source (7,668 lines, 105 Python files)
- ✅ 7 tagged releases (v0.1.0 → v0.7.0)
- ✅ 124 tests (via `.github/workflows/ci.yml`)
- ✅ MIT license
- ✅ 9 docs files under `docs/`
- ✅ Working installer + launcher
- ✅ Self-contained HTML dashboard

Recommended follow-up:

```bash
# Enable GitHub Actions (already configured in .github/workflows/ci.yml)
# Go to your repo → Actions tab → click "I understand my workflows, enable them"

# Set up a release from the v0.7.0 tag:
gh release create v0.7.0 --generate-notes
```

---

## 🐛 Troubleshooting

**"remote origin already exists"**
The script handles this via `git remote set-url`. If doing it manually:
```bash
git remote remove origin
git remote add origin https://github.com/your-github-username/Monad-Ultron.git
```

**"failed to push some refs" / "non-fast-forward"**
GitHub has an initial commit (README etc.) that conflicts. Either:
- Delete the GitHub repo and recreate it EMPTY, OR
- Force-push (destroys the GitHub-side README): `git push -u origin main --force`

**Auth prompt keeps failing**
Use a Personal Access Token, not your GitHub password. Create one at https://github.com/settings/tokens.
