# TickerPulse AI - Master Build Script
# Runs all 4 build stages to produce the Windows installer.
#
# Usage: .\scripts\build-all.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot

Write-Host ""
Write-Host "========================================" -ForegroundColor White
Write-Host "  TickerPulse AI - Desktop Build" -ForegroundColor White
Write-Host "========================================" -ForegroundColor White
Write-Host ""

$StartTime = Get-Date

# Stage 1: Backend
Write-Host "[1/4] Building backend with PyInstaller..." -ForegroundColor Cyan
& "$ScriptDir\build-backend.ps1"
Write-Host ""

# Stage 2: Frontend
Write-Host "[2/4] Building frontend with Next.js..." -ForegroundColor Cyan
& "$ScriptDir\build-frontend.ps1"
Write-Host ""

# Stage 3: Electron
Write-Host "[3/4] Compiling Electron main process..." -ForegroundColor Cyan
& "$ScriptDir\build-electron.ps1"
Write-Host ""

# Stage 4: Installer
Write-Host "[4/4] Packaging Windows installer..." -ForegroundColor Cyan
& "$ScriptDir\build-installer.ps1"
Write-Host ""

$Duration = [math]::Round(((Get-Date) - $StartTime).TotalMinutes, 1)

Write-Host "========================================" -ForegroundColor White
Write-Host "  Build Complete ($Duration min)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor White
Write-Host ""
Write-Host "  Installer: dist-electron\TickerPulse-AI-Setup-3.0.0.exe"
Write-Host ""
