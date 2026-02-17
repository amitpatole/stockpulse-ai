# TickerPulse AI - Package Windows Installer (NSIS)
# Produces: dist-electron/TickerPulse-AI-Setup-3.0.0.exe

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "[installer] Packaging with electron-builder..." -ForegroundColor Cyan

# Verify build artifacts exist
$BackendExe = "$ProjectRoot\build\backend\tickerpulse-backend\tickerpulse-backend.exe"
$FrontendServer = "$ProjectRoot\build\frontend\server.js"
$ElectronDist = "$ProjectRoot\electron\dist\main\index.js"

$Missing = @()
if (-not (Test-Path $BackendExe)) { $Missing += "Backend ($BackendExe)" }
if (-not (Test-Path $FrontendServer)) { $Missing += "Frontend ($FrontendServer)" }
if (-not (Test-Path $ElectronDist)) { $Missing += "Electron ($ElectronDist)" }

if ($Missing.Count -gt 0) {
    Write-Host "[installer] ERROR: Missing build artifacts:" -ForegroundColor Red
    foreach ($m in $Missing) { Write-Host "  - $m" -ForegroundColor Red }
    Write-Host "Run build-all.ps1 to build everything first." -ForegroundColor Yellow
    exit 1
}

Push-Location "$ProjectRoot\electron"
npx electron-builder --win --config electron-builder.yml
Pop-Location

$InstallerDir = "$ProjectRoot\dist-electron"
if (Test-Path $InstallerDir) {
    $Exe = Get-ChildItem $InstallerDir -Filter "*.exe" | Select-Object -First 1
    if ($Exe) {
        $Size = [math]::Round($Exe.Length / 1MB, 1)
        Write-Host "[installer] Build complete: $($Exe.FullName) ($Size MB)" -ForegroundColor Green
    }
} else {
    Write-Host "[installer] WARNING: dist-electron directory not found" -ForegroundColor Yellow
}
