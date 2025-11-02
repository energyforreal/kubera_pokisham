# PowerShell script to start and manage the trading bot
# This provides better process control and signal handling

param(
    [switch]$Safe = $true,
    [switch]$Force = $false
)

Write-Host "Starting Trading Bot..." -ForegroundColor Green

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python version: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if bot is already running
$existingProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*main.py*" -or $_.CommandLine -like "*run_bot_safe.py*"
}

if ($existingProcesses -and -not $Force) {
    Write-Host "Warning: Trading bot appears to be already running!" -ForegroundColor Yellow
    Write-Host "Processes found:" -ForegroundColor Yellow
    $existingProcesses | Format-Table Id, ProcessName, StartTime
    Write-Host "Use -Force to start anyway, or stop existing processes first" -ForegroundColor Yellow
    exit 1
}

# Kill existing processes if Force is specified
if ($existingProcesses -and $Force) {
    Write-Host "Stopping existing trading bot processes..." -ForegroundColor Yellow
    $existingProcesses | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# Start the bot
if ($Safe) {
    Write-Host "Starting with safe signal handling..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop gracefully" -ForegroundColor Cyan
    Write-Host "If Ctrl+C doesn't work, close this window" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        python run_bot_safe.py
    } catch {
        Write-Host "Error starting safe bot: $_" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Starting with standard signal handling..." -ForegroundColor Green
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        python src/main.py
    } catch {
        Write-Host "Error starting bot: $_" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Trading Bot has stopped." -ForegroundColor Green
