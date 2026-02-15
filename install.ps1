# ============================================================
# StockPulse AI v3.0 - Installer
# Windows PowerShell
# ============================================================
#
# Usage:
#   .\install.ps1              (from inside the repo)
#
# If you get an ExecutionPolicy error, run:
#   Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
#
# This script:
#   1. Checks prerequisites (Python 3.10+, Node 18+, npm)
#   2. Creates a Python virtual environment & installs backend deps
#   3. Installs frontend npm packages & builds the Next.js app
#   4. Copies .env.example -> .env (if .env doesn't exist)
# ============================================================

$ErrorActionPreference = "Stop"

# ── Helpers ────────────────────────────────────────────────

function Write-Info  { Write-Host "[INFO]  " -ForegroundColor Cyan -NoNewline; Write-Host $args }
function Write-Ok    { Write-Host "[OK]    " -ForegroundColor Green -NoNewline; Write-Host $args }
function Write-Warn  { Write-Host "[WARN]  " -ForegroundColor Yellow -NoNewline; Write-Host $args }
function Write-Err   { Write-Host "[ERROR] " -ForegroundColor Red -NoNewline; Write-Host $args }

function Test-CommandExists($cmd) {
    $null -ne (Get-Command $cmd -ErrorAction SilentlyContinue)
}

# ── Banner ─────────────────────────────────────────────────

Write-Host ""
Write-Host "========================================" -ForegroundColor White
Write-Host "  StockPulse AI v3.0 — Installer" -ForegroundColor White
Write-Host "========================================" -ForegroundColor White
Write-Host ""

# ── Prerequisite Checks ───────────────────────────────────

$Missing = 0

# Python — try 'python' first (Windows default), then 'python3'
$PythonCmd = $null
foreach ($cmd in @("python", "python3")) {
    if (Test-CommandExists $cmd) {
        $PyVerRaw = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($PyVerRaw) {
            $PyVer = [version]$PyVerRaw
            if ($PyVer -ge [version]"3.10") {
                $PythonCmd = $cmd
                Write-Ok "Python $PyVerRaw ($cmd)"
                break
            } else {
                Write-Err "Python $PyVerRaw found — need 3.10+"
                $Missing = 1
            }
        }
    }
}
if (-not $PythonCmd -and $Missing -eq 0) {
    Write-Err "Python not found"
    $Missing = 1
}

# Node.js
if (Test-CommandExists "node") {
    $NodeVerRaw = (node -v).TrimStart("v")
    $NodeMajor = [int]($NodeVerRaw.Split(".")[0])
    if ($NodeMajor -ge 18) {
        Write-Ok "Node.js $NodeVerRaw"
    } else {
        Write-Err "Node.js $NodeVerRaw found — need 18+"
        $Missing = 1
    }
} else {
    Write-Err "Node.js not found"
    $Missing = 1
}

# npm
if (Test-CommandExists "npm") {
    $NpmVer = npm -v
    Write-Ok "npm $NpmVer"
} else {
    Write-Err "npm not found"
    $Missing = 1
}

if ($Missing -ne 0) {
    Write-Host ""
    Write-Err "Missing prerequisites. Please install them first:"
    Write-Host "  Python 3.10+  — https://www.python.org/downloads/"
    Write-Host "  Node.js 18+   — https://nodejs.org/"
    exit 1
}

# ── Determine Install Directory ───────────────────────────

$RepoUrl = "https://github.com/amitpatole/stockpulse-ai.git"

if ((Test-Path "backend\app.py") -and (Test-Path "frontend\package.json")) {
    $ProjectDir = Get-Location
    Write-Info "Detected existing repo at $ProjectDir"
} else {
    if (-not (Test-CommandExists "git")) {
        Write-Err "git is required to clone the repo. Install it from https://git-scm.com/"
        exit 1
    }
    Write-Info "Cloning StockPulse AI..."
    git clone $RepoUrl stockpulse-ai
    $ProjectDir = Join-Path (Get-Location) "stockpulse-ai"
    Set-Location $ProjectDir
    Write-Ok "Cloned to $ProjectDir"
}

# ── Python Virtual Environment ────────────────────────────

Write-Host ""
Write-Info "Setting up Python virtual environment..."

if (Test-Path "venv") {
    Write-Warn "venv\ already exists — reusing"
} else {
    & $PythonCmd -m venv venv
    Write-Ok "Created venv\"
}

# Activate
& ".\venv\Scripts\Activate.ps1"

Write-Info "Upgrading pip..."
pip install --upgrade pip --quiet

Write-Info "Installing backend dependencies..."
pip install -r backend\requirements.txt --quiet
Write-Ok "Backend dependencies installed"

# ── Frontend Setup ─────────────────────────────────────────

Write-Host ""
Write-Info "Installing frontend dependencies..."

Push-Location "frontend"
npm install --silent 2>&1 | Select-Object -Last 1
Write-Ok "Frontend npm packages installed"

Write-Info "Building frontend (this may take a minute)..."
npm run build
Write-Ok "Frontend built"

Pop-Location

# ── Environment Configuration ──────────────────────────────

Write-Host ""
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Ok "Created .env from .env.example"
} else {
    Write-Warn ".env already exists — skipping copy"
}

# ── Done ───────────────────────────────────────────────────

Write-Host ""
Write-Host "========================================" -ForegroundColor White
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor White
Write-Host ""
Write-Host "  Next steps:"
Write-Host ""
Write-Host "  1. " -NoNewline; Write-Host "Edit .env" -ForegroundColor Yellow -NoNewline; Write-Host " and add at least one AI provider API key"
Write-Host "     (Anthropic, OpenAI, Google, or xAI)"
Write-Host ""
Write-Host "  2. Start the application:"
Write-Host "     " -NoNewline; Write-Host ".\run.sh" -ForegroundColor Cyan -NoNewline; Write-Host "  (Git Bash / WSL)"
Write-Host "     or run backend and frontend separately:"
Write-Host "     " -NoNewline; Write-Host "cd backend; python app.py" -ForegroundColor Cyan
Write-Host "     " -NoNewline; Write-Host "cd frontend; npm run start" -ForegroundColor Cyan
Write-Host ""
Write-Host "  3. Open in your browser:"
Write-Host "     " -NoNewline; Write-Host "http://localhost:3000" -ForegroundColor Cyan
Write-Host ""
