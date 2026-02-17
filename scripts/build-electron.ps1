# TickerPulse AI - Compile Electron Main Process
# Produces: electron/dist/ with compiled TypeScript

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path $PSScriptRoot -Parent

Write-Host "[electron] Compiling TypeScript..." -ForegroundColor Cyan

Push-Location "$ProjectRoot\electron"
npm ci --silent
npx tsc
Pop-Location

Write-Host "[electron] Compile complete" -ForegroundColor Green
