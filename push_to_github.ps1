# push_to_github.ps1 — Push blog files to bhagya.engineer GitHub repo
# Run from PowerShell: .\push_to_github.ps1
# Or from Command Prompt: powershell -ExecutionPolicy Bypass -File push_to_github.ps1

$REPO   = "NARASIMHASAINATHNVL/bhagya-website"
$BASE   = "https://api.github.com"
$BRANCH = "main"
$HERE   = $PSScriptRoot
if (-not $HERE) { $HERE = Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $HERE) { $HERE = (Get-Location).Path }

$FILES = @(
    @{
        GhPath    = "blog/admin.html"
        LocalPath = Join-Path $HERE "blog\admin.html"
        Commit    = "feat: add blog/admin.html — protected dashboard with Quill editor"
    },
    @{
        GhPath    = "blog/posts.json"
        LocalPath = Join-Path $HERE "blog\posts.json"
        Commit    = "fix: update blog/posts.json — full article content"
    }
)

function Push-File($Token, $GhPath, $LocalPath, $CommitMsg) {
    $Headers = @{
        "Authorization" = "token $Token"
        "Accept"        = "application/vnd.github.v3+json"
        "Content-Type"  = "application/json"
    }

    $Bytes      = [System.IO.File]::ReadAllBytes($LocalPath)
    $ContentB64 = [Convert]::ToBase64String($Bytes)

    # Get existing SHA (if file already on GitHub)
    try {
        $GetR = Invoke-RestMethod -Uri "$BASE/repos/$REPO/contents/$GhPath" -Headers $Headers -Method Get -ErrorAction Stop
        $Sha  = $GetR.sha
        $Action = "Updated"
    } catch {
        $Sha  = $null
        $Action = "Created"
    }

    $Body = @{ message = $CommitMsg; content = $ContentB64; branch = $BRANCH }
    if ($Sha) { $Body["sha"] = $Sha }

    $BodyJson = $Body | ConvertTo-Json -Compress

    try {
        $PutR = Invoke-RestMethod -Uri "$BASE/repos/$REPO/contents/$GhPath" -Headers $Headers -Method Put -Body $BodyJson -ErrorAction Stop
        Write-Host "  [OK] $Action`: $GhPath" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  [FAIL] $GhPath — $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

Write-Host ""
Write-Host ("=" * 55)
Write-Host "  bhagya.engineer — GitHub Push Script (PowerShell)"
Write-Host ("=" * 55)
Write-Host ""

# Prompt for PAT (masked)
$SecurePat = Read-Host "Paste your GitHub PAT" -AsSecureString
$Token = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecurePat)
)

if (-not $Token) {
    Write-Host "No token entered. Exiting." -ForegroundColor Yellow
    exit 1
}

# Verify token
try {
    $Me = Invoke-RestMethod -Uri "$BASE/user" -Headers @{
        "Authorization" = "token $Token"
        "Accept"        = "application/vnd.github.v3+json"
    } -Method Get -ErrorAction Stop
    Write-Host "Authenticated as: $($Me.login)" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "[ERROR] Token invalid or no API access" -ForegroundColor Red
    exit 1
}

$Success = 0
foreach ($F in $FILES) {
    if (-not (Test-Path $F.LocalPath)) {
        Write-Host "  [SKIP] Not found: $($F.LocalPath)" -ForegroundColor Yellow
        continue
    }
    $SizeKB = [math]::Round((Get-Item $F.LocalPath).Length / 1024, 1)
    Write-Host "Pushing $($F.GhPath) ($SizeKB KB) ..."
    if (Push-File $Token $F.GhPath $F.LocalPath $F.Commit) {
        $Success++
    }
}

Write-Host ""
Write-Host "Result: $Success/$($FILES.Count) files pushed to GitHub." -ForegroundColor Cyan

if ($Success -gt 0) {
    Write-Host ""
    Write-Host "Vercel will auto-deploy in ~30 seconds." -ForegroundColor Green
    Write-Host ""
    Write-Host "Live URLs once deployed:"
    Write-Host "  Blog front:  https://bhagya.engineer/blog/"
    Write-Host "  Admin panel: https://bhagya.engineer/blog/admin.html"
    Write-Host "  Sample post: https://bhagya.engineer/blog/post.html?id=technical-seo-errors-fintech"
}

Write-Host ""
Read-Host "Press Enter to close"
