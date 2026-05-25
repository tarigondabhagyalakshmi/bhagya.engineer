# push_blog_redesign.ps1
# Pushes the newly redesigned blog/index.html and blog/admin.html to GitHub

$REPO   = "NARASIMHASAINATHNVL/bhagya-website"
$BASE   = "https://api.github.com"
$HERE   = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $HERE) { $HERE = (Get-Location).Path }
$PAT_FILE = Join-Path $HERE "pat.txt"

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  bhagya.engineer — Push Blog Redesign" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# ── Load PAT ──
if (Test-Path $PAT_FILE) {
    $TOKEN = (Get-Content $PAT_FILE -Raw).Trim()
    Write-Host "PAT loaded from pat.txt" -ForegroundColor Green
} else {
    $SecurePAT = Read-Host "Paste your GitHub PAT" -AsSecureString
    $TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePAT)
    )
    if (-not $TOKEN) { Write-Host "No token. Exiting." -ForegroundColor Red; exit 1 }
    $TOKEN | Out-File -FilePath $PAT_FILE -Encoding UTF8 -NoNewline
}

$Headers = @{
    "Authorization" = "token $TOKEN"
    "Accept"        = "application/vnd.github.v3+json"
    "Content-Type"  = "application/json"
}

# ── Verify token ──
try {
    $Me = Invoke-RestMethod -Uri "$BASE/user" -Headers $Headers -Method Get -ErrorAction Stop
    Write-Host "Authenticated as: $($Me.login)" -ForegroundColor Cyan
} catch {
    Write-Host "[ERROR] Token invalid. Delete pat.txt and run again." -ForegroundColor Red
    exit 1
}

# ── Files to push ──
$FILES = @(
    @{ GhPath="blog/index.html"; Local=Join-Path $HERE "blog\index.html"; Msg="redesign: blog frontend — Ink & Gold editorial theme" },
    @{ GhPath="blog/admin.html"; Local=Join-Path $HERE "blog\admin.html"; Msg="redesign: admin dashboard — clean SaaS UI" }
)

$Success = 0
foreach ($F in $FILES) {
    if (-not (Test-Path $F.Local)) {
        Write-Host "  [SKIP] Not found: $($F.Local)" -ForegroundColor Yellow
        continue
    }
    $SizeKB = [math]::Round((Get-Item $F.Local).Length / 1024, 1)
    Write-Host "Pushing $($F.GhPath) ($SizeKB KB)..." -NoNewline

    # Read as UTF-8 text, trim trailing null chars, re-encode cleanly
    $TextContent = [System.IO.File]::ReadAllText($F.Local, [System.Text.Encoding]::UTF8).TrimEnd([char]0)
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($TextContent)
    $ContentB64 = [Convert]::ToBase64String($Bytes)

    # Get SHA
    try {
        $GetR = Invoke-RestMethod -Uri "$BASE/repos/$REPO/contents/$($F.GhPath)" -Headers $Headers -Method Get -ErrorAction Stop
        $Sha = $GetR.sha
    } catch { $Sha = $null }

    $Body = @{ message=$F.Msg; content=$ContentB64; branch="main" }
    if ($Sha) { $Body["sha"] = $Sha }

    try {
        $null = Invoke-RestMethod -Uri "$BASE/repos/$REPO/contents/$($F.GhPath)" -Headers $Headers -Method Put -Body ($Body | ConvertTo-Json -Compress) -ErrorAction Stop
        Write-Host " OK" -ForegroundColor Green
        $Success++
    } catch {
        Write-Host " FAILED: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
if ($Success -eq $FILES.Count) {
    Write-Host "All $Success files pushed!" -ForegroundColor Green
    Write-Host "Vercel deploys in ~30 seconds." -ForegroundColor Green
    Write-Host ""
    Write-Host "  Blog:  https://bhagya.engineer/blog/" -ForegroundColor Cyan
    Write-Host "  Admin: https://bhagya.engineer/blog/admin.html" -ForegroundColor Cyan
} else {
    Write-Host "$Success/$($FILES.Count) files pushed." -ForegroundColor Yellow
}

Write-Host ""
Read-Host "Press Enter to close"
