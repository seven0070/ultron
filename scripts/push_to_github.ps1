# =============================================================================
#  Monad-Ultron — one-shot GitHub push script (Windows PowerShell)
# =============================================================================
#  Usage:
#    .\scripts\push_to_github.ps1 -Username <your-github-username> [-Repo Monad-Ultron]
#
#  Prerequisites (do these FIRST):
#    A. Create an empty repo on GitHub:
#         https://github.com/new
#         Do NOT initialize with README / .gitignore / LICENSE
#    B. Auth: `gh auth login` OR git credential manager set up
# =============================================================================

param(
    [Parameter(Mandatory=$true)]
    [string]$Username,

    [string]$Repo = "Monad-Ultron"
)

$ErrorActionPreference = "Stop"

# Move to repo root
Set-Location -Path (Join-Path $PSScriptRoot "..")
$RepoRoot = (Get-Location).Path

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Monad-Ultron → GitHub" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  Username:  $Username"
Write-Host "  Repo:      $Repo"
Write-Host "  Root:      $RepoRoot"
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# --- Sanity ------------------------------------------------------------------

if (-not (Test-Path ".git")) {
    Write-Host "[X] not a git repo. Aborting." -ForegroundColor Red
    exit 1
}

$dirty = git status --porcelain
if ($dirty) {
    Write-Host "[!] working tree has uncommitted changes:" -ForegroundColor Yellow
    Write-Host $dirty
    $ans = Read-Host "    Continue anyway? [y/N]"
    if ($ans -notin @("y", "Y")) { exit 1 }
}

# --- 1. Replace placeholder --------------------------------------------------

Write-Host "[1/4] Replacing YOUR_USERNAME → $Username …"

$targets = Get-ChildItem -Recurse -File `
    -Exclude "push_to_github.ps1", "push_to_github.sh" `
    | Where-Object {
        $_.FullName -notmatch "\\\.git\\" -and
        $_.FullName -notmatch "\\\.venv\\" -and
        $_.FullName -notmatch "\\__pycache__\\" -and
        $_.FullName -notmatch "\\models\\" -and
        $_.FullName -notmatch "\\memory_data\\" -and
        $_.FullName -notmatch "\\python_portable\\"
    }

$changed = 0
foreach ($f in $targets) {
    try {
        $content = Get-Content $f.FullName -Raw -ErrorAction Stop
        if ($content -match "YOUR_USERNAME") {
            $new = $content -replace "YOUR_USERNAME", $Username
            Set-Content -Path $f.FullName -Value $new -NoNewline
            Write-Host "      · $($f.FullName.Substring($RepoRoot.Length + 1))"
            $changed++
        }
    } catch {
        # skip binary files silently
    }
}
if ($changed -eq 0) {
    Write-Host "      (no YOUR_USERNAME placeholders found — already personalized?)"
}

# --- 2. Commit ---------------------------------------------------------------

Write-Host ""
Write-Host "[2/4] Committing personalization …"

$dirty = git status --porcelain
if ($dirty) {
    git add -A
    git commit -q -m "Personalize repo URLs for $Username/$Repo"
    Write-Host "      committed."
} else {
    Write-Host "      nothing to commit."
}

# --- 3. Remote ---------------------------------------------------------------

Write-Host ""
Write-Host "[3/4] Configuring 'origin' remote …"

$remoteUrl = "https://github.com/$Username/$Repo.git"

$hasOrigin = git remote 2>$null | Select-String -Pattern "^origin$" -Quiet
if ($hasOrigin) {
    git remote set-url origin $remoteUrl
    Write-Host "      updated to $remoteUrl"
} else {
    git remote add origin $remoteUrl
    Write-Host "      added $remoteUrl"
}

$currentBranch = git rev-parse --abbrev-ref HEAD
if ($currentBranch -ne "main") {
    Write-Host "      renaming '$currentBranch' → 'main'"
    git branch -M main
}

# --- 4. Push -----------------------------------------------------------------

Write-Host ""
Write-Host "[4/4] Pushing to GitHub …"
Write-Host "      (if this hangs, run 'gh auth login' first)"
Write-Host ""

git push -u origin main
git push origin --tags

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ✔ pushed!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Repo:      https://github.com/$Username/$Repo"
Write-Host "  Actions:   https://github.com/$Username/$Repo/actions"
Write-Host "  Releases:  https://github.com/$Username/$Repo/releases"
Write-Host "============================================================" -ForegroundColor Green
