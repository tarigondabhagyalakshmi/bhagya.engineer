# SYNC.ps1 — Auto-push bhagya-website to GitHub → Vercel
# ─────────────────────────────────────────────────────────────
# First run:  saves your GitHub PAT to pat.txt (not uploaded to GitHub)
# Every run:  git init (if needed) → pull → commit all changes → push
# ─────────────────────────────────────────────────────────────

$REPO_DIR   = "C:\Users\DELL\Documents\Claud-Global\bhagya-website-main"
$GH_USER    = "nuvvulasainath"
$GH_ORG     = "NARASIMHASAINATHNVL"
$GH_REPO    = "bhagya-website"
$BRANCH     = "main"
$PAT_FILE   = Join-Path $REPO_DIR "pat.txt"

Set-Location $REPO_DIR

function Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$ts] $msg"
}

# ── 1. Load or prompt for PAT ────────────────────────────────────────────────
if (Test-Path $PAT_FILE) {
    $TOKEN = (Get-Content $PAT_FILE -Raw).Trim()
    Log "Using saved PAT from pat.txt"
} else {
    Write-Host ""
    Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  First-time setup: GitHub PAT needed" -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Go to: github.com → Settings → Developer Settings"
    Write-Host "       → Personal access tokens → Classic → Generate"
    Write-Host "       → Scopes: check 'repo' → Generate & Copy"
    Write-Host ""
    $SecurePAT = Read-Host "Paste your GitHub PAT" -AsSecureString
    $TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePAT)
    )
    if (-not $TOKEN) { Write-Host "No PAT entered. Exiting." -ForegroundColor Red; exit 1 }
    $TOKEN | Out-File -FilePath $PAT_FILE -Encoding UTF8 -NoNewline
    Log "PAT saved to pat.txt (will not be pushed to GitHub)"
}

$REMOTE_URL = "https://${GH_USER}:${TOKEN}@github.com/${GH_ORG}/${GH_REPO}.git"

# ── 2. Check git is installed ────────────────────────────────────────────────
try {
    $null = git --version 2>&1
} catch {
    Write-Host ""
    Write-Host "Git is not installed!" -ForegroundColor Red
    Write-Host "Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    Write-Host "Install it, then run SYNC.bat again." -ForegroundColor Yellow
    Read-Host "Press Enter to close"
    exit 1
}

# ── 3. Init git repo if not already ─────────────────────────────────────────
$isGitRepo = git rev-parse --is-inside-work-tree 2>&1
if ($LASTEXITCODE -ne 0) {
    Log "Initializing git repo for the first time..."
    git init
    git config user.name "Sai"
    git config user.email "narasimha.sainath@bankbazaar.com"
    git remote add origin $REMOTE_URL

    # Ensure .gitignore has pat.txt so the token is never uploaded
    $gitignorePath = Join-Path $REPO_DIR ".gitignore"
    if (-not (Test-Path $gitignorePath)) {
        "pat.txt`npush_to_github.py`npush_to_github.ps1`n" | Out-File $gitignorePath -Encoding UTF8
    } else {
        $content = Get-Content $gitignorePath -Raw
        if ($content -notmatch "pat\.txt") {
            "`npat.txt" | Add-Content $gitignorePath
        }
    }

    # Fetch and track remote branch
    git fetch origin $BRANCH
    git checkout -b $BRANCH --track "origin/$BRANCH" 2>&1
    if ($LASTEXITCODE -ne 0) {
        git checkout $BRANCH 2>&1
    }
    Log "Git repo initialized and connected to GitHub."
} else {
    # Repo exists — just update remote URL with fresh token
    git remote set-url origin $REMOTE_URL
}

# ── 4. Pull latest first (avoid conflicts) ───────────────────────────────────
Log "Pulling latest from GitHub..."
git pull origin $BRANCH --rebase 2>&1 | ForEach-Object { "  $_" } | Write-Host

# ── 5. Check for changes ─────────────────────────────────────────────────────
$changes = git status --porcelain 2>&1
if (-not $changes) {
    Log "No changes detected — everything is up to date."
    Write-Host ""
    Write-Host "Site is live at: https://bhagya.engineer" -ForegroundColor Green
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 0
}

Log "Changes found:"
$changes | ForEach-Object { Write-Host "  $_" }

# ── 6. Stage all changes ──────────────────────────────────────────────────────
git add -A

# ── 7. Commit ─────────────────────────────────────────────────────────────────
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
$msg = "Auto-push: website update [$timestamp]"
git commit -m $msg
if ($LASTEXITCODE -ne 0) {
    Log "Nothing new to commit (already up to date)."
    exit 0
}

# ── 8. Push ───────────────────────────────────────────────────────────────────
Log "Pushing to GitHub..."
git push origin $BRANCH
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "  ✅ Pushed successfully!" -ForegroundColor Green
    Write-Host "  Vercel deploys in ~30 seconds." -ForegroundColor Green
    Write-Host "  Live at: https://bhagya.engineer" -ForegroundColor Cyan
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "  ❌ Push failed. Check your PAT — it may have expired." -ForegroundColor Red
    Write-Host "  Delete pat.txt and run SYNC.bat again to enter a new PAT." -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Press Enter to close"
