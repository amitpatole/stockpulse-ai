# StockPulse AI - Build Frontend (Next.js Standalone)
# Produces: build/frontend/ with server.js, .next/static/, public/, node.exe

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "[frontend] Building Next.js standalone..." -ForegroundColor Cyan

# Build Next.js
Push-Location "$ProjectRoot\frontend"
npm ci --silent
npm run build
Pop-Location

# Create output directory
$OutDir = "$ProjectRoot\build\frontend"
if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# Copy standalone output
# Next.js nests under the workspace name, so server.js may be at standalone/frontend/
$StandalonePath = "$ProjectRoot\frontend\.next\standalone"
$ServerJsPaths = @(
    "$StandalonePath\server.js",
    "$StandalonePath\frontend\server.js"
)

$FoundPath = $null
foreach ($p in $ServerJsPaths) {
    if (Test-Path $p) {
        $FoundPath = Split-Path $p -Parent
        break
    }
}

if (-not $FoundPath) {
    Write-Host "[frontend] ERROR: standalone server.js not found. Ensure next.config.ts has output: 'standalone'" -ForegroundColor Red
    exit 1
}

Copy-Item -Recurse -Force "$FoundPath\*" $OutDir

# Copy static assets (standalone does not include these)
New-Item -ItemType Directory -Force -Path "$OutDir\.next\static" | Out-Null
Copy-Item -Recurse -Force "$ProjectRoot\frontend\.next\static\*" "$OutDir\.next\static\"

# Copy public assets
if (Test-Path "$ProjectRoot\frontend\public") {
    Copy-Item -Recurse -Force "$ProjectRoot\frontend\public" "$OutDir\public"
}

# Download Node.js Windows binary for bundling
$NodeVersion = "v22.14.0"
$NodeExe = "$OutDir\node.exe"

if (-not (Test-Path $NodeExe)) {
    $TempDir = "$ProjectRoot\build\temp"
    New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

    $NodeUrl = "https://nodejs.org/dist/$NodeVersion/win-x64/node.exe"
    Write-Host "[frontend] Downloading Node.js $NodeVersion..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri $NodeUrl -OutFile $NodeExe
}

$Size = [math]::Round((Get-ChildItem $OutDir -Recurse | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host "[frontend] Build complete: $OutDir ($Size MB)" -ForegroundColor Green
