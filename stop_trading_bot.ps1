# PowerShell script to stop the trading bot
# This provides better process detection and cleanup

param(
    [switch]$Force = $false,
    [switch]$All = $false
)

# Set encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

# Get project root (assume script is in project root or scripts folder)
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = if (Test-Path (Join-Path $scriptPath "..\src")) { 
    Split-Path -Parent $scriptPath 
} else { 
    $scriptPath 
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     🛑 STOPPING TRADING AGENT SYSTEM 🛑" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STOP SYSTEM MONITOR
# ============================================================================

$monitorPidFile = Join-Path $projectRoot "logs\system_monitor.pid"

if (Test-Path $monitorPidFile) {
    Write-Host "🛑 Stopping System Monitor..." -ForegroundColor Cyan
    
    try {
        $monitorPid = Get-Content $monitorPidFile -ErrorAction SilentlyContinue
        if ($monitorPid) {
            $monitorProcess = Get-Process -Id $monitorPid -ErrorAction SilentlyContinue
            if ($monitorProcess) {
                Write-Host "    Found monitor process (PID: $monitorPid)" -ForegroundColor Gray
                
                # Try graceful shutdown first
                $monitorProcess | Stop-Process -Force -ErrorAction SilentlyContinue
                Start-Sleep -Seconds 2
                
                # Check if still running
                $stillRunning = Get-Process -Id $monitorPid -ErrorAction SilentlyContinue
                if ($stillRunning) {
                    Write-Host "    Force stopping monitor..." -ForegroundColor Yellow
                    $stillRunning | Stop-Process -Force
                }
                
                Write-Host "    ✅ System Monitor stopped" -ForegroundColor Green
            } else {
                Write-Host "    ⚠️  Monitor process not found (may already be stopped)" -ForegroundColor Yellow
            }
            
            # Remove PID file
            Remove-Item $monitorPidFile -ErrorAction SilentlyContinue
        }
    } catch {
        Write-Host "    ⚠️  Error stopping monitor: $_" -ForegroundColor Yellow
    }
    
    Write-Host ""
} else {
    # Try to find monitor process by name
    $monitorProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*system_monitor*" -or
        $_.CommandLine -like "*src.monitoring.system_monitor*"
    }
    
    if ($monitorProcesses) {
        Write-Host "🛑 Stopping System Monitor (found by process name)..." -ForegroundColor Cyan
        $monitorProcesses | Stop-Process -Force
        Write-Host "    ✅ System Monitor stopped" -ForegroundColor Green
        Write-Host ""
    }
}

# ============================================================================
# STOP BACKEND API
# ============================================================================

Write-Host "🛑 Stopping Backend API..." -ForegroundColor Yellow

$backendProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*Backend API*" -or
    $_.Path -like "*backend\api\main.py"
}

if ($backendProcesses) {
    Write-Host "    Found Backend API processes: $($backendProcesses.Count)" -ForegroundColor Gray
    $backendProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "    ✅ Backend API stopped" -ForegroundColor Green
} else {
    Write-Host "    ℹ️  No Backend API processes found" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# STOP FRONTEND WEB
# ============================================================================

Write-Host "🛑 Stopping Frontend Web..." -ForegroundColor Yellow

$frontendProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*Frontend Web*"
}

if ($frontendProcesses) {
    Write-Host "    Found Frontend Web processes: $($frontendProcesses.Count)" -ForegroundColor Gray
    $frontendProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "    ✅ Frontend Web stopped" -ForegroundColor Green
} else {
    Write-Host "    ℹ️  No Frontend Web processes found" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# STOP DIAGNOSTIC SERVICE
# ============================================================================

Write-Host "🛑 Stopping Diagnostic Service..." -ForegroundColor Yellow

$diagnosticProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*Diagnostic Service*"
}

if ($diagnosticProcesses) {
    Write-Host "    Found Diagnostic Service processes: $($diagnosticProcesses.Count)" -ForegroundColor Gray
    $diagnosticProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "    ✅ Diagnostic Service stopped" -ForegroundColor Green
} else {
    Write-Host "    ℹ️  No Diagnostic Service processes found" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# STOP DIAGNOSTIC DASHBOARD
# ============================================================================

Write-Host "🛑 Stopping Diagnostic Dashboard..." -ForegroundColor Yellow

$diagnosticDashboardProcesses = Get-Process node -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*Diagnostic Dashboard*"
}

if ($diagnosticDashboardProcesses) {
    Write-Host "    Found Diagnostic Dashboard processes: $($diagnosticDashboardProcesses.Count)" -ForegroundColor Gray
    $diagnosticDashboardProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "    ✅ Diagnostic Dashboard stopped" -ForegroundColor Green
} else {
    Write-Host "    ℹ️  No Diagnostic Dashboard processes found" -ForegroundColor Gray
}

Write-Host ""

# ============================================================================
# STOP TRADING BOT
# ============================================================================

Write-Host "🛑 Stopping Trading Bot..." -ForegroundColor Yellow

$tradingProcesses = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
    $_.MainWindowTitle -like "*Trading Bot*"
}

if ($tradingProcesses) {
    Write-Host "    Found Trading Bot processes: $($tradingProcesses.Count)" -ForegroundColor Gray
    $tradingProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "    ✅ Trading Bot stopped" -ForegroundColor Green
} else {
    Write-Host "    ℹ️  No Trading Bot processes found" -ForegroundColor Gray
}

Write-Host ""

# If --all flag is used, kill all Python and Node processes
if ($All) {
    Write-Host "🛑 Stopping ALL Python and Node processes..." -ForegroundColor Red
    $pythonProcs = Get-Process python -ErrorAction SilentlyContinue
    $nodeProcs = Get-Process node -ErrorAction SilentlyContinue
    
    if ($pythonProcs) {
        Write-Host "    Stopping $($pythonProcs.Count) Python processes..." -ForegroundColor Yellow
        $pythonProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    
    if ($nodeProcs) {
        Write-Host "    Stopping $($nodeProcs.Count) Node processes..." -ForegroundColor Yellow
        $nodeProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "    ✅ All processes stopped" -ForegroundColor Green
    Write-Host ""
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     ✅ SHUTDOWN COMPLETE ✅" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "All services stopped successfully." -ForegroundColor Green
Write-Host ""
