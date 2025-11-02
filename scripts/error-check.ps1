# PowerShell wrapper for error-check.py
# Provides better Windows integration and output formatting

param(
    [switch]$Verbose = $false,
    [int]$MaxIterations = 5,
    [string]$ApiUrl = "http://localhost:8000"
)

# Set encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

# Change to project root directory
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                  🔍 TRADING AGENT ERROR CHECK SYSTEM 🔍" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Check Python availability
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found!" -ForegroundColor Red
    Write-Host "   Please install Python 3.8+ to run error checking" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Build Python command
$pythonScript = Join-Path $projectRoot "scripts\error-check.py"
$env:API_URL = $ApiUrl

$pythonArgs = @()
if ($MaxIterations -ne 5) {
    # Note: MaxIterations is hardcoded in Python script, but we can pass via env
    $env:MAX_ITERATIONS = $MaxIterations.ToString()
}

# Run Python script
Write-Host "Running error check system..." -ForegroundColor Cyan
Write-Host ""

try {
    $output = python $pythonScript 2>&1
    
    # Display output
    $output | ForEach-Object {
        Write-Host $_
    }
    
    # Check exit code
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host "                              ✅ ERROR CHECK COMPLETE ✅" -ForegroundColor Green
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Green
        Write-Host ""
        Write-Host "💡 Check error_check_results.json for detailed results" -ForegroundColor Cyan
    } else {
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host "                           ⚠️  ERRORS REMAIN AFTER CHECK ⚠️" -ForegroundColor Yellow
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "💡 Review error_check_results.json for details and fix manually" -ForegroundColor Yellow
    }
    
    exit $LASTEXITCODE
    
} catch {
    Write-Host ""
    Write-Host "❌ Error running check script: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

