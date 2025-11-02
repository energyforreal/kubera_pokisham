# PowerShell script to start all components of the Trading Agent system
# and open the frontend in the browser

param(
    [switch]$Minimize = $true,
    [switch]$SkipChecks = $false,
    [switch]$EnableMonitoring = $true,
    [int]$FrontendPort = 3000,
    [int]$BackendPort = 8000,
    [int]$DiagnosticPort = 8080,
    [int]$DiagnosticDashboardPort = 3001
)

# Set encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ErrorActionPreference = "Continue"

# Change to project root directory
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     🚀 STARTING TRADING AGENT SYSTEM 🚀" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

function Test-Port {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName localhost -Port $Port -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
        return $connection.TcpTestSucceeded
    } catch {
        return $false
    }
}

function Wait-ForService {
    param(
        [string]$ServiceName,
        [string]$Url,
        [int]$MaxRetries = 30,
        [int]$RetryDelay = 2
    )
    
    Write-Host "    ⏳ Waiting for $ServiceName..." -ForegroundColor Yellow -NoNewline
    
    for ($i = 1; $i -le $MaxRetries; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host " ✅ Ready!" -ForegroundColor Green
                return $true
            }
        } catch {
            Start-Sleep -Seconds $RetryDelay
            Write-Host "." -ForegroundColor Gray -NoNewline
        }
    }
    
    Write-Host " ⚠️  Timeout" -ForegroundColor Yellow
    return $false
}

function Start-Component {
    param(
        [string]$Name,
        [string]$Command,
        [string]$WorkingDirectory = $projectRoot,
        [string]$Title,
        [switch]$CheckPort = $false,
        [int]$Port = 0
    )
    
    Write-Host ""
    Write-Host "[$Name] Starting..." -ForegroundColor Yellow
    
    # Check if port is already in use
    if ($CheckPort -and $Port -gt 0) {
        if (Test-Port -Port $Port) {
            Write-Host "    ⚠️  Port $Port is already in use. Service may already be running." -ForegroundColor Yellow
            return $null
        }
    }
    
    # Prepare window style
    $windowStyle = if ($Minimize) { "Minimized" } else { "Normal" }
    
    # Prepare command arguments - use here-string to avoid PowerShell parsing issues
    $cmdString = @"
chcp 65001 >nul 2>&1 && cd /d "$WorkingDirectory" && title $Title && $Command
"@
    $cmdArgs = "/k", $cmdString
    
    try {
        $process = Start-Process -FilePath "cmd" -ArgumentList $cmdArgs -WindowStyle $windowStyle -PassThru
        Write-Host "    ✅ Started (PID: $($process.Id))" -ForegroundColor Green
        return $process
    } catch {
        Write-Host "    ❌ Failed to start: $_" -ForegroundColor Red
        return $null
    }
}

function Open-Browser {
    param([string]$Url)
    
    Write-Host ""
    Write-Host "🌐 Opening frontend in browser..." -ForegroundColor Cyan
    
    try {
        # Try using Cursor browser tools first (if available via MCP)
        # Fallback to default browser
        Start-Process $Url
        Write-Host "    ✅ Browser opened: $Url" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "    ⚠️  Failed to open browser automatically. Please open manually: $Url" -ForegroundColor Yellow
        Write-Host "    📋 URL: $Url" -ForegroundColor Cyan
        return $false
    }
}

# ============================================================================
# PRE-FLIGHT CHECKS
# ============================================================================

if (-not $SkipChecks) {
    Write-Host "🔍 Pre-flight checks..." -ForegroundColor Blue
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ Python: $pythonVersion" -ForegroundColor Green
        } else {
            throw "Python not found"
        }
    } catch {
        Write-Host "    ❌ Python not found!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Check Node.js
    try {
        $nodeVersion = node --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "    ✅ Node.js: $nodeVersion" -ForegroundColor Green
        } else {
            throw "Node.js not found"
        }
    } catch {
        Write-Host "    ❌ Node.js not found!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Check if ports are available
    Write-Host ""
    Write-Host "🔌 Checking ports..." -ForegroundColor Blue
    
    $ports = @(
        @{Port = $BackendPort; Service = "Backend API"},
        @{Port = $FrontendPort; Service = "Frontend Web"},
        @{Port = $DiagnosticPort; Service = "Diagnostic Service"},
        @{Port = $DiagnosticDashboardPort; Service = "Diagnostic Dashboard"}
    )
    
    foreach ($portInfo in $ports) {
        if (Test-Port -Port $portInfo.Port) {
            Write-Host "    ⚠️  Port $($portInfo.Port) ($($portInfo.Service)) is in use" -ForegroundColor Yellow
        } else {
            Write-Host "    ✅ Port $($portInfo.Port) ($($portInfo.Service)) is available" -ForegroundColor Green
        }
    }
    
    Write-Host ""
}

# ============================================================================
# START COMPONENTS
# ============================================================================

Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     🚀 STARTING COMPONENTS 🚀" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$processes = @{}

# 1. Start Trading Bot
$processes.TradingBot = Start-Component `
    -Name "Trading Bot" `
    -Command "python src\main.py" `
    -WorkingDirectory $projectRoot `
    -Title "Trading Agent - Trading Bot" `
    -CheckPort $false
Start-Sleep -Seconds 3

# 2. Start Backend API
$processes.BackendAPI = Start-Component `
    -Name "Backend API" `
    -Command "set PYTHONPATH=%CD% && python backend\api\main.py" `
    -WorkingDirectory $projectRoot `
    -Title "Trading Agent - Backend API (Port $BackendPort)" `
    -CheckPort $true `
    -Port $BackendPort
Start-Sleep -Seconds 8

# 3. Start Diagnostic Service
if (Test-Path "diagnostic_service\package.json") {
    $processes.DiagnosticService = Start-Component `
        -Name "Diagnostic Service" `
        -Command "npm start" `
        -WorkingDirectory "$projectRoot\diagnostic_service" `
        -Title "Trading Agent - Diagnostic Service (Port $DiagnosticPort)" `
        -CheckPort $true `
        -Port $DiagnosticPort
    Start-Sleep -Seconds 5
} else {
    Write-Host ""
    Write-Host "[Diagnostic Service] ⚠️  Skipped (package.json not found)" -ForegroundColor Yellow
}

# 4. Start Frontend Web
if (Test-Path "frontend_web\package.json") {
    $processes.FrontendWeb = Start-Component `
        -Name "Frontend Web" `
        -Command "npm run dev" `
        -WorkingDirectory "$projectRoot\frontend_web" `
        -Title "Trading Agent - Frontend Web (Port $FrontendPort)" `
        -CheckPort $true `
        -Port $FrontendPort
    Start-Sleep -Seconds 3
} else {
    Write-Host ""
    Write-Host "[Frontend Web] ⚠️  Skipped (package.json not found)" -ForegroundColor Yellow
}

# 5. Start Diagnostic Dashboard
if (Test-Path "diagnostic_dashboard\package.json") {
    $processes.DiagnosticDashboard = Start-Component `
        -Name "Diagnostic Dashboard" `
        -Command "npm run dev -- --port $DiagnosticDashboardPort" `
        -WorkingDirectory "$projectRoot\diagnostic_dashboard" `
        -Title "Trading Agent - Diagnostic Dashboard (Port $DiagnosticDashboardPort)" `
        -CheckPort $true `
        -Port $DiagnosticDashboardPort
    Start-Sleep -Seconds 3
} else {
    Write-Host ""
    Write-Host "[Diagnostic Dashboard] ⚠️  Skipped (package.json not found)" -ForegroundColor Yellow
}

# ============================================================================
# HEALTH CHECKS
# ============================================================================

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     🔍 HEALTH CHECKS 🔍" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Wait for Backend API
Wait-ForService -ServiceName "Backend API" -Url "http://localhost:$BackendPort/api/v1/health"

# Wait for Frontend Web
$frontendReady = Wait-ForService -ServiceName "Frontend Web" -Url "http://localhost:$FrontendPort"

# ============================================================================
# OPEN BROWSER
# ============================================================================

if ($frontendReady) {
    Open-Browser -Url "http://localhost:$FrontendPort"
} else {
    Write-Host ""
    Write-Host "⚠️  Frontend may still be starting. Opening browser anyway..." -ForegroundColor Yellow
    Open-Browser -Url "http://localhost:$FrontendPort"
}

# ============================================================================
# SYSTEM MONITOR
# ============================================================================

$monitorProcess = $null

if ($EnableMonitoring) {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "                     🔍 STARTING SYSTEM MONITOR 🔍" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        # Check if monitor config exists
        $monitorConfig = Join-Path $projectRoot "config\monitor_config.yaml"
        if (-not (Test-Path $monitorConfig)) {
            Write-Host "    ⚠️  Monitor config not found: $monitorConfig" -ForegroundColor Yellow
            Write-Host "    ℹ️  Monitor will use default configuration" -ForegroundColor Gray
        }
        
        # Start system monitor as background process
        Write-Host "    🔄 Starting System Monitor..." -ForegroundColor Yellow -NoNewline
        
        $monitorArgs = @(
            "-m", "src.monitoring.system_monitor"
            "--interval", "30"
        )
        
        # Use hidden window to run in background
        $monitorProcess = Start-Process python -ArgumentList $monitorArgs -PassThru -WindowStyle Hidden -WorkingDirectory $projectRoot
        
        # Wait a moment to see if it starts successfully
        Start-Sleep -Seconds 2
        
        if ($monitorProcess.HasExited) {
            Write-Host " ❌ Failed to start" -ForegroundColor Red
            Write-Host "    ⚠️  Monitor process exited immediately. Check logs for errors." -ForegroundColor Yellow
            $monitorProcess = $null
        } else {
            Write-Host " ✅ Running (PID: $($monitorProcess.Id))" -ForegroundColor Green
            Write-Host "    ℹ️  Monitor will continuously check component health and auto-restart on failures" -ForegroundColor Gray
            
            # Save monitor PID to file for stop script
            $monitorPidFile = Join-Path $projectRoot "logs\system_monitor.pid"
            $monitorProcess.Id | Out-File -FilePath $monitorPidFile -Encoding UTF8 -Force
        }
        
    } catch {
        Write-Host " ❌ Error: $_" -ForegroundColor Red
        Write-Host "    ⚠️  Monitoring will not be available. Services will continue running." -ForegroundColor Yellow
        $monitorProcess = $null
    }
    
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "⚠️  System monitoring disabled (--EnableMonitoring:$false)" -ForegroundColor Yellow
    Write-Host ""
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "                     ✅ SYSTEM STARTUP COMPLETE ✅" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 Services Status:" -ForegroundColor Green
Write-Host ""

$serviceUrls = @(
    @{Name = "Trading Bot"; Status = if ($processes.TradingBot) { "✅ Running" } else { "❌ Not Started" }; URL = "N/A"},
    @{Name = "Backend API"; Status = if ($processes.BackendAPI) { "✅ Running" } else { "⚠️  Check Status" }; URL = "http://localhost:$BackendPort"},
    @{Name = "Diagnostic Service"; Status = if ($processes.DiagnosticService) { "✅ Running" } else { "⚠️  Skipped/Not Started" }; URL = "http://localhost:$DiagnosticPort"},
    @{Name = "Frontend Web"; Status = if ($processes.FrontendWeb) { "✅ Running" } else { "⚠️  Check Status" }; URL = "http://localhost:$FrontendPort"},
    @{Name = "Diagnostic Dashboard"; Status = if ($processes.DiagnosticDashboard) { "✅ Running" } else { "⚠️  Skipped/Not Started" }; URL = "http://localhost:$DiagnosticDashboardPort"}
)

# Add System Monitor to status
if ($EnableMonitoring) {
    $serviceUrls += @{Name = "System Monitor"; Status = if ($monitorProcess) { "✅ Running" } else { "⚠️  Not Started" }; URL = "N/A"}
}

foreach ($service in $serviceUrls) {
    Write-Host "    $($service.Status) - $($service.Name)" -ForegroundColor $(if ($service.Status -like "*✅*") { "Green" } else { "Yellow" })
    if ($service.URL -ne "N/A") {
        Write-Host "        📍 $($service.URL)" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "🌐 Access Points:" -ForegroundColor Cyan
Write-Host "    🖥️  Main Dashboard:        http://localhost:$FrontendPort" -ForegroundColor White
Write-Host "    📊 Diagnostic Dashboard:   http://localhost:$DiagnosticDashboardPort" -ForegroundColor White
Write-Host "    🔧 API Documentation:     http://localhost:$BackendPort/docs" -ForegroundColor White
Write-Host "    ❤️  Health Check:         http://localhost:$BackendPort/api/v1/health" -ForegroundColor White
Write-Host "    📈 Diagnostic API:        http://localhost:$DiagnosticPort/api" -ForegroundColor White
Write-Host ""
Write-Host "💡 Tips:" -ForegroundColor Yellow
Write-Host "    • All services are running in separate windows (minimized if -Minimize flag used)" -ForegroundColor Gray
Write-Host "    • To stop services, close the individual windows or use Ctrl+C in each window" -ForegroundColor Gray
if ($EnableMonitoring -and $monitorProcess) {
    Write-Host "    • System Monitor is running and will auto-restart failed components" -ForegroundColor Gray
    Write-Host "    • Monitor logs: logs/system_monitor_*.json" -ForegroundColor Gray
}
Write-Host "    • Wait 30-45 seconds for all services to fully initialize" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"

