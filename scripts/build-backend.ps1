# TickerPulse AI - Build Backend (PyInstaller)
# Produces: build/backend/tickerpulse-backend/

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "[backend] Building with PyInstaller..." -ForegroundColor Cyan

# Activate venv
if (Test-Path "$ProjectRoot\venv\Scripts\Activate.ps1") {
    & "$ProjectRoot\venv\Scripts\Activate.ps1"
} else {
    Write-Host "[backend] No venv found — using system Python" -ForegroundColor Yellow
}

# Install PyInstaller if needed
pip install pyinstaller --quiet

# Clean previous build
$OutDir = "$ProjectRoot\build\backend"
$TempDir = "$ProjectRoot\build\temp\backend"
if (Test-Path $OutDir) { Remove-Item $OutDir -Recurse -Force }

# Run PyInstaller from project root
Push-Location $ProjectRoot
pyinstaller backend\tickerpulse.spec --distpath "$OutDir" --workpath "$TempDir" -y
Pop-Location

$ExePath = "$OutDir\tickerpulse-backend\tickerpulse-backend.exe"
if (Test-Path $ExePath) {
    $Size = [math]::Round((Get-ChildItem $OutDir -Recurse | Measure-Object Length -Sum).Sum / 1MB, 1)
    Write-Host "[backend] Build complete: $ExePath ($Size MB)" -ForegroundColor Green
} else {
    Write-Host "[backend] Build FAILED — exe not found" -ForegroundColor Red
    exit 1
}
