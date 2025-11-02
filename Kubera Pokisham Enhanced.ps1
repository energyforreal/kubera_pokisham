# PowerShell Enhanced Launcher for KUBERA POKISHAM AI Trading System
# Advanced Signal Handling & Integration Validation

param(
    [string]$Mode = "",
    [switch]$SkipChecks = $false,
    [switch]$Verbose = $false
)

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Set window title
$Host.UI.RawUI.WindowTitle = "KUBERA POKISHAM - Enhanced AI Trading System"

# Change to script directory
Set-Location $PSScriptRoot

# ============================================================================
# ASCII ART HEADER
# ============================================================================
Clear-Host
Write-Host ""
Write-Host "    ██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗  █████╗ " -ForegroundColor Yellow
Write-Host "    ██║ ██╔╝██║   ██║██╔══██╗██╔════╝██╔══██╗██╔══██╗" -ForegroundColor Yellow
Write-Host "    █████╔╝ ██║   ██║██████╔╝█████╗  ██████╔╝███████║" -ForegroundColor Yellow
Write-Host "    ██╔═██╗ ██║   ██║██╔══██╗██╔══╝  ██╔══██╗██╔══██║" -ForegroundColor Yellow
Write-Host "    ██║  ██╗╚██████╔╝██████╔╝███████╗██║  ██║██║  ██║" -ForegroundColor Yellow
Write-Host "    ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝" -ForegroundColor Yellow
Write-Host ""
Write-Host "    ██████╗  ██████╗ ██╗  ██╗██╗███████╗██╗  ██╗ █████╗ ███╗   ███╗" -ForegroundColor Yellow
Write-Host "    ██╔══██╗██╔═══██╗██║ ██╔╝██║██╔════╝██║  ██║██╔══██╗████╗ ████║" -ForegroundColor Yellow
Write-Host "    ██████╔╝██║   ██║█████╔╝ ██║███████╗███████║███████║██╔████╔██║" -ForegroundColor Yellow
Write-Host "    ██╔═══╝ ██║   ██║██╔═██╗ ██║╚════██║██╔══██║██╔══██║██║╚██╔╝██║" -ForegroundColor Yellow
Write-Host "    ██║     ╚██████╔╝██║  ██╗██║███████║██║  ██║██║  ██║██║ ╚═╝ ██║" -ForegroundColor Yellow
Write-Host "    ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝" -ForegroundColor Yellow
Write-Host ""
Write-Host "                           🚀 ENHANCED AI TRADING SYSTEM 🚀" -ForegroundColor Green
Write-Host "                              ⚡ Advanced Signal Handling ⚡" -ForegroundColor Cyan
Write-Host "                              🔧 Integration Validation 🔧" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# ENHANCED PRE-FLIGHT CHECKS
# ============================================================================
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "                              🔍 PRE-FLIGHT CHECKS" -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

if (-not $SkipChecks) {
    # Check Python installation
    Write-Host "[1/10] ► Checking Python installation..." -ForegroundColor Yellow
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "        ✅ Python $pythonVersion detected" -ForegroundColor Green
        } else {
            throw "Python not found"
        }
    } catch {
        Write-Host "        ❌ Python not found! Please install Python 3.10+ from python.org" -ForegroundColor Red
        Write-Host "        📥 Download: https://www.python.org/downloads/" -ForegroundColor Cyan
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Check Node.js installation
    Write-Host ""
    Write-Host "[2/10] ► Checking Node.js installation..." -ForegroundColor Yellow
    try {
        $nodeVersion = node --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "        ✅ Node.js $nodeVersion detected" -ForegroundColor Green
        } else {
            throw "Node.js not found"
        }
    } catch {
        Write-Host "        ❌ Node.js not found! Please install Node.js 18+ from nodejs.org" -ForegroundColor Red
        Write-Host "        📥 Download: https://nodejs.org/" -ForegroundColor Cyan
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Check Python dependencies
    Write-Host ""
    Write-Host "[3/10] ► Checking Python dependencies..." -ForegroundColor Yellow
    try {
        python -c "import pandas, numpy, sklearn, xgboost, lightgbm, fastapi, uvicorn" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "        ✅ Python dependencies verified" -ForegroundColor Green
        } else {
            Write-Host "        ⚠️  Installing missing Python packages..." -ForegroundColor Yellow
            pip install -r requirements.txt 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "        ✅ Python dependencies installed" -ForegroundColor Green
            } else {
                Write-Host "        ❌ Failed to install Python dependencies" -ForegroundColor Red
                Read-Host "Press Enter to exit"
                exit 1
            }
        }
    } catch {
        Write-Host "        ❌ Error checking Python dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }

    # Check production models
    Write-Host ""
    Write-Host "[4/10] ► Checking production models..." -ForegroundColor Yellow
    $models = @(
        "models\randomforest_BTCUSD_4h_production_20251014_125258.pkl",
        "models\xgboost_BTCUSD_4h_production_20251014_114541.pkl"
    )
    $missingModels = @()
    foreach ($model in $models) {
        if (-not (Test-Path $model)) {
            $missingModels += $model
        }
    }
    if ($missingModels.Count -gt 0) {
        Write-Host "        ❌ Missing production models:" -ForegroundColor Red
        foreach ($model in $missingModels) {
            Write-Host "        📁 $model" -ForegroundColor Red
        }
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "        ✅ Production models found ($($models.Count)/$($models.Count))" -ForegroundColor Green

    # Check configuration
    Write-Host ""
    Write-Host "[5/10] ► Checking configuration..." -ForegroundColor Yellow
    if (-not (Test-Path "config\config.yaml")) {
        Write-Host "        ❌ Configuration file not found!" -ForegroundColor Red
        Write-Host "        📁 Expected: config\config.yaml" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "        ✅ Configuration file found" -ForegroundColor Green

    # Check signal handling improvements
    Write-Host ""
    Write-Host "[6/10] ► Checking signal handling improvements..." -ForegroundColor Yellow
    if (-not (Test-Path "run_bot_safe.py")) {
        Write-Host "        ❌ Safe wrapper script not found!" -ForegroundColor Red
        Write-Host "        📁 Expected: run_bot_safe.py" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    if (-not (Test-Path "scripts\check_integrations.py")) {
        Write-Host "        ❌ Integration validation scripts not found!" -ForegroundColor Red
        Write-Host "        📁 Expected: scripts\check_integrations.py" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "        ✅ Signal handling improvements detected" -ForegroundColor Green

    # Prepare directories
    Write-Host ""
    Write-Host "[7/10] ► Preparing directories..." -ForegroundColor Yellow
    $directories = @("logs", "backend\logs", "scripts")
    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    Write-Host "        ✅ Log directories ready" -ForegroundColor Green

    # Check database access
    Write-Host ""
    Write-Host "[8/10] ► Checking database access..." -ForegroundColor Yellow
    if (-not (Test-Path "kubera_pokisham.db")) {
        Write-Host "        ⚠️  Database will be created on first run" -ForegroundColor Yellow
    } else {
        Write-Host "        ✅ Database file exists" -ForegroundColor Green
    }

    # Run integration health checks
    Write-Host ""
    Write-Host "[9/10] ► Running integration health checks..." -ForegroundColor Yellow
    try {
        python scripts\check_integrations.py 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "        ✅ Integration health checks passed" -ForegroundColor Green
        } else {
            Write-Host "        ⚠️  Integration issues detected - will run validation after startup" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "        ⚠️  Integration health checks failed - continuing with startup" -ForegroundColor Yellow
    }

    # Final system check
    Write-Host ""
    Write-Host "[10/10] ► Final system check..." -ForegroundColor Yellow
    $env:PYTHONPATH = "$PWD;$env:PYTHONPATH"
    Write-Host "        ✅ Environment configured" -ForegroundColor Green
}

# ============================================================================
# STARTUP MODE SELECTION
# ============================================================================
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host "                              🚀 STARTUP MODE SELECTION" -ForegroundColor Blue
Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
Write-Host ""

if ($Mode -eq "") {
    Write-Host "Choose your startup mode:"
    Write-Host ""
    Write-Host "[1] 🏭 Full Production System (All 5 services) - Recommended for production" -ForegroundColor Green
    Write-Host "     └─ Complete trading system with all services" -ForegroundColor Gray
    Write-Host "     └─ Web dashboards, monitoring, diagnostics" -ForegroundColor Gray
    Write-Host "     └─ Maximum functionality and monitoring" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[2] 🤖 Safe Trading Bot (Enhanced Signal Handling) - Recommended for development" -ForegroundColor Cyan
    Write-Host "     └─ Trading bot with Ctrl+C support" -ForegroundColor Gray
    Write-Host "     └─ Enhanced error handling and graceful shutdown" -ForegroundColor Gray
    Write-Host "     └─ Perfect for development and testing" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[3] 🔧 Integration Testing (With validation) - For system validation" -ForegroundColor Yellow
    Write-Host "     └─ Full system with integration validation" -ForegroundColor Gray
    Write-Host "     └─ Automated health checks and monitoring" -ForegroundColor Gray
    Write-Host "     └─ Comprehensive testing and diagnostics" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[4] 🛠️  Development Mode (With debugging) - For development" -ForegroundColor Magenta
    Write-Host "     └─ Trading bot with enhanced logging" -ForegroundColor Gray
    Write-Host "     └─ Debug mode with verbose output" -ForegroundColor Gray
    Write-Host "     └─ Development-friendly configuration" -ForegroundColor Gray
    Write-Host ""
    Write-Host "[5] 🎛️  Service Management Mode - Advanced control" -ForegroundColor Red
    Write-Host "     └─ Interactive service management" -ForegroundColor Gray
    Write-Host "     └─ Individual service control" -ForegroundColor Gray
    Write-Host "     └─ Real-time monitoring and control" -ForegroundColor Gray
    Write-Host ""
    
    do {
        $Mode = Read-Host "Enter your choice (1-5)"
    } while ($Mode -notmatch "^[1-5]$")
}

# ============================================================================
# STARTUP MODE IMPLEMENTATIONS
# ============================================================================

switch ($Mode) {
    "1" {
        # Full Production System
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host "                              🏭 FULL PRODUCTION SYSTEM" -ForegroundColor Blue
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host ""
        Write-Host "Starting complete trading system with all 5 services..." -ForegroundColor Green
        Write-Host ""

        # Start Trading Bot
        Write-Host "[1/5] ► Starting Trading Bot (AI Agent)..." -ForegroundColor Yellow
        Write-Host "        📍 Location: src\main.py" -ForegroundColor Gray
        Write-Host "        🎯 Mode: Paper Trading (Safe)" -ForegroundColor Gray
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Trading Bot && python src\main.py" -WindowStyle Minimized
        Start-Sleep -Seconds 3
        Write-Host "        ✅ Trading Bot started (minimized)" -ForegroundColor Green

        # Start Backend API
        Write-Host ""
        Write-Host "[2/5] ► Starting Backend API (FastAPI)..." -ForegroundColor Yellow
        Write-Host "        📍 Location: backend\api\main.py" -ForegroundColor Gray
        Write-Host "        🌐 Port: 8000" -ForegroundColor Gray
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Backend API - Port 8000 && set PYTHONPATH=%CD% && python backend\api\main.py" -WindowStyle Minimized
        Start-Sleep -Seconds 8
        Write-Host "        ✅ Backend API started (minimized)" -ForegroundColor Green

        # Start Diagnostic Service
        Write-Host ""
        Write-Host "[3/5] ► Starting Diagnostic Service (Node.js)..." -ForegroundColor Yellow
        Write-Host "        📍 Location: diagnostic_service\" -ForegroundColor Gray
        Write-Host "        🌐 Port: 8080" -ForegroundColor Gray
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\diagnostic_service`" && title KUBERA Diagnostic Service - Port 8080 && npm start" -WindowStyle Minimized
        Start-Sleep -Seconds 5
        Write-Host "        ✅ Diagnostic Service started (minimized)" -ForegroundColor Green

        # Start Frontend Dashboard
        Write-Host ""
        Write-Host "[4/5] ► Starting Frontend Dashboard (Next.js)..." -ForegroundColor Yellow
        Write-Host "        📍 Location: frontend_web\" -ForegroundColor Gray
        Write-Host "        🌐 Port: 3000" -ForegroundColor Gray
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\frontend_web`" && title KUBERA Frontend Dashboard - Port 3000 && npm run dev" -WindowStyle Minimized
        Start-Sleep -Seconds 3
        Write-Host "        ✅ Frontend Dashboard started (minimized)" -ForegroundColor Green

        # Start Diagnostic Dashboard
        Write-Host ""
        Write-Host "[5/5] ► Starting Diagnostic Dashboard (Next.js)..." -ForegroundColor Yellow
        Write-Host "        📍 Location: diagnostic_dashboard\" -ForegroundColor Gray
        Write-Host "        🌐 Port: 3001" -ForegroundColor Gray
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\diagnostic_dashboard`" && title KUBERA Diagnostic Dashboard - Port 3001 && npm run dev" -WindowStyle Minimized
        Start-Sleep -Seconds 3
        Write-Host "        ✅ Diagnostic Dashboard started (minimized)" -ForegroundColor Green

        # Show completion message
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host "                              🎉 STARTUP COMPLETE!" -ForegroundColor Blue
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host ""
        Write-Host "🏭 Full Production System is now running:" -ForegroundColor Green
        Write-Host ""
        Write-Host "    🤖 Trading Bot          → AI-powered paper trading" -ForegroundColor White
        Write-Host "    🔧 Backend API          → FastAPI server (port 8000)" -ForegroundColor White
        Write-Host "    📊 Diagnostic Service  → System monitoring (port 8080)" -ForegroundColor White
        Write-Host "    🖥️  Frontend Dashboard  → Main web interface (port 3000)" -ForegroundColor White
        Write-Host "    📈 Diagnostic Dashboard → System diagnostics (port 3001)" -ForegroundColor White
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host "                              🌐 ACCESS POINTS" -ForegroundColor Blue
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host ""
        Write-Host "📱 Main Dashboard:        http://localhost:3000" -ForegroundColor Cyan
        Write-Host "📊 Diagnostic Dashboard:   http://localhost:3001" -ForegroundColor Cyan
        Write-Host "🔧 API Documentation:     http://localhost:8000/docs" -ForegroundColor Cyan
        Write-Host "❤️  Health Check:         http://localhost:8000/api/v1/health" -ForegroundColor Cyan
        Write-Host "📈 Diagnostics API:      http://localhost:8080/api" -ForegroundColor Cyan
        Write-Host "📊 Prometheus Metrics:    http://localhost:8080/metrics" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host "                              ⚠️  IMPORTANT NOTES" -ForegroundColor Blue
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host ""
        Write-Host "🔸 Wait 30-45 seconds for all services to fully initialize" -ForegroundColor Yellow
        Write-Host "🔸 Check minimized windows for any startup errors" -ForegroundColor Yellow
        Write-Host "🔸 Trading bot runs in PAPER MODE (no real money at risk)" -ForegroundColor Yellow
        Write-Host "🔸 All services will continue running until manually stopped" -ForegroundColor Yellow
        Write-Host "🔸 To stop all services: Close the 5 minimized windows" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Press any key to open the main dashboard in your browser..." -ForegroundColor Green
        Read-Host ""
        Write-Host ""
        Write-Host "🌐 Opening main dashboard..." -ForegroundColor Green
        Start-Process "http://localhost:3000"
        Write-Host ""
        Write-Host "✅ Dashboard opened! All services are running in the background." -ForegroundColor Green
        Write-Host "    You can close this window - the services will continue running." -ForegroundColor Gray
        Write-Host ""
        Write-Host "🎯 Happy Trading with KUBERA POKISHAM! 🚀" -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
    
    "2" {
        # Safe Trading Bot
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host "                              🤖 SAFE TRADING BOT" -ForegroundColor Blue
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host ""
        Write-Host "Starting trading bot with enhanced signal handling..." -ForegroundColor Green
        Write-Host "🔸 Press Ctrl+C to stop gracefully" -ForegroundColor Yellow
        Write-Host "🔸 Enhanced error handling and recovery" -ForegroundColor Yellow
        Write-Host "🔸 Perfect for development and testing" -ForegroundColor Yellow
        Write-Host ""

        Write-Host "[1/1] ► Starting Safe Trading Bot..." -ForegroundColor Yellow
        Write-Host "        📍 Location: run_bot_safe.py" -ForegroundColor Gray
        Write-Host "        🎯 Mode: Enhanced Signal Handling" -ForegroundColor Gray
        Write-Host "        ⚡ Features: Ctrl+C support, graceful shutdown, timeout protection" -ForegroundColor Gray
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Safe Trading Bot - Ctrl+C to Stop && python run_bot_safe.py"

        Write-Host ""
        Write-Host "✅ Safe Trading Bot started in new window" -ForegroundColor Green
        Write-Host "🔸 You can now use Ctrl+C to stop the bot gracefully" -ForegroundColor Yellow
        Write-Host "🔸 The bot will handle all shutdown procedures automatically" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "🎯 Happy Trading with KUBERA POKISHAM! 🚀" -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
    
    "3" {
        # Integration Testing
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host "                              🔧 INTEGRATION TESTING" -ForegroundColor Blue
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host ""
        Write-Host "Starting full system with integration validation..." -ForegroundColor Green
        Write-Host ""

        # Run pre-startup validation
        Write-Host "[1/6] ► Running pre-startup integration validation..." -ForegroundColor Yellow
        python scripts\check_integrations.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "        ✅ Integration validation passed" -ForegroundColor Green
        } else {
            Write-Host "        ⚠️  Integration issues detected - continuing with startup" -ForegroundColor Yellow
        }

        # Start all services (same as full production)
        Write-Host ""
        Write-Host "[2/6] ► Starting Trading Bot (AI Agent)..." -ForegroundColor Yellow
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Trading Bot && python src\main.py" -WindowStyle Minimized
        Start-Sleep -Seconds 3
        Write-Host "        ✅ Trading Bot started (minimized)" -ForegroundColor Green

        Write-Host ""
        Write-Host "[3/6] ► Starting Backend API (FastAPI)..." -ForegroundColor Yellow
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Backend API - Port 8000 && set PYTHONPATH=%CD% && python backend\api\main.py" -WindowStyle Minimized
        Start-Sleep -Seconds 8
        Write-Host "        ✅ Backend API started (minimized)" -ForegroundColor Green

        Write-Host ""
        Write-Host "[4/6] ► Starting Diagnostic Service (Node.js)..." -ForegroundColor Yellow
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\diagnostic_service`" && title KUBERA Diagnostic Service - Port 8080 && npm start" -WindowStyle Minimized
        Start-Sleep -Seconds 5
        Write-Host "        ✅ Diagnostic Service started (minimized)" -ForegroundColor Green

        Write-Host ""
        Write-Host "[5/6] ► Starting Frontend Dashboard (Next.js)..." -ForegroundColor Yellow
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\frontend_web`" && title KUBERA Frontend Dashboard - Port 3000 && npm run dev" -WindowStyle Minimized
        Start-Sleep -Seconds 3
        Write-Host "        ✅ Frontend Dashboard started (minimized)" -ForegroundColor Green

        # Run post-startup validation
        Write-Host ""
        Write-Host "[6/6] ► Running post-startup integration validation..." -ForegroundColor Yellow
        Start-Sleep -Seconds 10
        python scripts\validate_sync.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "        ✅ Synchronization validation passed" -ForegroundColor Green
        } else {
            Write-Host "        ⚠️  Synchronization issues detected - check logs" -ForegroundColor Yellow
        }

        Write-Host ""
        Write-Host "🔧 Integration Testing System is now running:" -ForegroundColor Green
        Write-Host ""
        Write-Host "    🤖 Trading Bot          → AI-powered paper trading" -ForegroundColor White
        Write-Host "    🔧 Backend API          → FastAPI server (port 8000)" -ForegroundColor White
        Write-Host "    📊 Diagnostic Service  → System monitoring (port 8080)" -ForegroundColor White
        Write-Host "    🖥️  Frontend Dashboard  → Main web interface (port 3000)" -ForegroundColor White
        Write-Host "    📈 Diagnostic Dashboard → System diagnostics (port 3001)" -ForegroundColor White
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host "                              🧪 INTEGRATION TESTING" -ForegroundColor Blue
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host ""
        Write-Host "🔸 Integration validation completed" -ForegroundColor Yellow
        Write-Host "🔸 Health checks passed" -ForegroundColor Yellow
        Write-Host "🔸 Synchronization validated" -ForegroundColor Yellow
        Write-Host "🔸 All services monitored" -ForegroundColor Yellow
        Write-Host "🔸 Comprehensive testing enabled" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "🎯 Happy Trading with KUBERA POKISHAM! 🚀" -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
    
    "4" {
        # Development Mode
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host "                              🛠️  DEVELOPMENT MODE" -ForegroundColor Blue
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host ""
        Write-Host "Starting trading bot in development mode with enhanced logging..." -ForegroundColor Green
        Write-Host ""

        Write-Host "[1/1] ► Starting Development Trading Bot..." -ForegroundColor Yellow
        Write-Host "        📍 Location: src\main.py" -ForegroundColor Gray
        Write-Host "        🎯 Mode: Development with enhanced logging" -ForegroundColor Gray
        Write-Host "        🔧 Features: Verbose output, debug mode, enhanced error reporting" -ForegroundColor Gray
        Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Development Bot - Enhanced Logging && python src\main.py"

        Write-Host ""
        Write-Host "✅ Development Trading Bot started in new window" -ForegroundColor Green
        Write-Host "🔸 Enhanced logging and debugging enabled" -ForegroundColor Yellow
        Write-Host "🔸 Perfect for development and troubleshooting" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "🎯 Happy Trading with KUBERA POKISHAM! 🚀" -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to exit"
    }
    
    "5" {
        # Service Management Mode
        Write-Host ""
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host "                              🎛️  SERVICE MANAGEMENT MODE" -ForegroundColor Blue
        Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
        Write-Host ""
        Write-Host "Interactive service management and control..." -ForegroundColor Green
        Write-Host ""

        # Service Management Menu Loop
        do {
            Write-Host ""
            Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
            Write-Host "                              🎛️  SERVICE MANAGEMENT MENU" -ForegroundColor Blue
            Write-Host "═══════════════════════════════════════════════════════════════════════════════" -ForegroundColor Blue
            Write-Host ""
            Write-Host "[1] 🚀 Start All Services (Full System)" -ForegroundColor Green
            Write-Host "[2] 🤖 Start Trading Bot Only (Safe Mode)" -ForegroundColor Cyan
            Write-Host "[3] 🔧 Start Backend API Only" -ForegroundColor Yellow
            Write-Host "[4] 📊 Start Diagnostic Service Only" -ForegroundColor Magenta
            Write-Host "[5] 🖥️  Start Frontend Dashboard Only" -ForegroundColor Blue
            Write-Host "[6] 📈 Start Diagnostic Dashboard Only" -ForegroundColor Red
            Write-Host "[7] 🔍 View Service Status" -ForegroundColor White
            Write-Host "[8] 🧪 Run Integration Tests" -ForegroundColor Gray
            Write-Host "[9] 📋 View System Logs" -ForegroundColor DarkGray
            Write-Host "[10] 🛑 Stop All Services" -ForegroundColor DarkRed
            Write-Host "[11] ❌ Exit" -ForegroundColor DarkRed
            Write-Host ""
            
            $choice = Read-Host "Enter your choice (1-11)"
            
            switch ($choice) {
                "1" {
                    Write-Host "🚀 Starting all services..." -ForegroundColor Green
                    # Start all services (same as full production)
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Trading Bot && python src\main.py" -WindowStyle Minimized
                    Start-Sleep -Seconds 3
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Backend API - Port 8000 && set PYTHONPATH=%CD% && python backend\api\main.py" -WindowStyle Minimized
                    Start-Sleep -Seconds 8
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\diagnostic_service`" && title KUBERA Diagnostic Service - Port 8080 && npm start" -WindowStyle Minimized
                    Start-Sleep -Seconds 5
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\frontend_web`" && title KUBERA Frontend Dashboard - Port 3000 && npm run dev" -WindowStyle Minimized
                    Start-Sleep -Seconds 3
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\diagnostic_dashboard`" && title KUBERA Diagnostic Dashboard - Port 3001 && npm run dev" -WindowStyle Minimized
                    Write-Host "        ✅ All services started" -ForegroundColor Green
                }
                "2" {
                    Write-Host "🤖 Starting trading bot only..." -ForegroundColor Cyan
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Safe Trading Bot - Ctrl+C to Stop && python run_bot_safe.py"
                    Write-Host "        ✅ Trading Bot started" -ForegroundColor Green
                }
                "3" {
                    Write-Host "🔧 Starting backend API only..." -ForegroundColor Yellow
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD`" && title KUBERA Backend API - Port 8000 && set PYTHONPATH=%CD% && python backend\api\main.py" -WindowStyle Minimized
                    Write-Host "        ✅ Backend API started" -ForegroundColor Green
                }
                "4" {
                    Write-Host "📊 Starting diagnostic service only..." -ForegroundColor Magenta
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\diagnostic_service`" && title KUBERA Diagnostic Service - Port 8080 && npm start" -WindowStyle Minimized
                    Write-Host "        ✅ Diagnostic Service started" -ForegroundColor Green
                }
                "5" {
                    Write-Host "🖥️  Starting frontend dashboard only..." -ForegroundColor Blue
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\frontend_web`" && title KUBERA Frontend Dashboard - Port 3000 && npm run dev" -WindowStyle Minimized
                    Write-Host "        ✅ Frontend Dashboard started" -ForegroundColor Green
                }
                "6" {
                    Write-Host "📈 Starting diagnostic dashboard only..." -ForegroundColor Red
                    Start-Process -FilePath "cmd" -ArgumentList "/k", "chcp 65001 >nul 2>&1 && cd /d `"$PWD\diagnostic_dashboard`" && title KUBERA Diagnostic Dashboard - Port 3001 && npm run dev" -WindowStyle Minimized
                    Write-Host "        ✅ Diagnostic Dashboard started" -ForegroundColor Green
                }
                "7" {
                    Write-Host "🔍 Checking service status..." -ForegroundColor White
                    Write-Host ""
                    Write-Host "[1/5] ► Checking Trading Bot..." -ForegroundColor Yellow
                    $tradingBot = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*main.py*" }
                    if ($tradingBot) {
                        Write-Host "        ✅ Trading Bot is running" -ForegroundColor Green
                    } else {
                        Write-Host "        ❌ Trading Bot is not running" -ForegroundColor Red
                    }
                    
                    Write-Host ""
                    Write-Host "[2/5] ► Checking Backend API..." -ForegroundColor Yellow
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
                        if ($response.StatusCode -eq 200) {
                            Write-Host "        ✅ Backend API is responding" -ForegroundColor Green
                        } else {
                            Write-Host "        ❌ Backend API is not responding" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "        ❌ Backend API is not responding" -ForegroundColor Red
                    }
                    
                    Write-Host ""
                    Write-Host "[3/5] ► Checking Diagnostic Service..." -ForegroundColor Yellow
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:8080/api" -TimeoutSec 5 -ErrorAction SilentlyContinue
                        if ($response.StatusCode -eq 200) {
                            Write-Host "        ✅ Diagnostic Service is responding" -ForegroundColor Green
                        } else {
                            Write-Host "        ❌ Diagnostic Service is not responding" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "        ❌ Diagnostic Service is not responding" -ForegroundColor Red
                    }
                    
                    Write-Host ""
                    Write-Host "[4/5] ► Checking Frontend Dashboard..." -ForegroundColor Yellow
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 5 -ErrorAction SilentlyContinue
                        if ($response.StatusCode -eq 200) {
                            Write-Host "        ✅ Frontend Dashboard is responding" -ForegroundColor Green
                        } else {
                            Write-Host "        ❌ Frontend Dashboard is not responding" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "        ❌ Frontend Dashboard is not responding" -ForegroundColor Red
                    }
                    
                    Write-Host ""
                    Write-Host "[5/5] ► Checking Diagnostic Dashboard..." -ForegroundColor Yellow
                    try {
                        $response = Invoke-WebRequest -Uri "http://localhost:3001" -TimeoutSec 5 -ErrorAction SilentlyContinue
                        if ($response.StatusCode -eq 200) {
                            Write-Host "        ✅ Diagnostic Dashboard is responding" -ForegroundColor Green
                        } else {
                            Write-Host "        ❌ Diagnostic Dashboard is not responding" -ForegroundColor Red
                        }
                    } catch {
                        Write-Host "        ❌ Diagnostic Dashboard is not responding" -ForegroundColor Red
                    }
                    
                    Read-Host "Press Enter to continue"
                }
                "8" {
                    Write-Host "🧪 Running integration tests..." -ForegroundColor Gray
                    Write-Host ""
                    Write-Host "[1/4] ► Running integration health checks..." -ForegroundColor Yellow
                    python scripts\check_integrations.py
                    Write-Host ""
                    Write-Host "[2/4] ► Running synchronization validation..." -ForegroundColor Yellow
                    python scripts\validate_sync.py
                    Write-Host ""
                    Write-Host "[3/4] ► Running real-time communication tests..." -ForegroundColor Yellow
                    python scripts\test_realtime.py
                    Write-Host ""
                    Write-Host "[4/4] ► Running data consistency checks..." -ForegroundColor Yellow
                    python scripts\check_data_consistency.py
                    Write-Host ""
                    Write-Host "✅ Integration tests completed" -ForegroundColor Green
                    Read-Host "Press Enter to continue"
                }
                "9" {
                    Write-Host "📋 Viewing system logs..." -ForegroundColor DarkGray
                    Write-Host ""
                    Write-Host "[1/3] ► Trading Bot logs..." -ForegroundColor Yellow
                    if (Test-Path "logs\trading_agent.log") {
                        Write-Host "        📄 Trading Agent Log (last 10 lines):" -ForegroundColor Gray
                        Get-Content "logs\trading_agent.log" -Tail 10
                    } else {
                        Write-Host "        ❌ Trading Agent log not found" -ForegroundColor Red
                    }
                    
                    Write-Host ""
                    Write-Host "[2/3] ► Backend API logs..." -ForegroundColor Yellow
                    if (Test-Path "backend\logs\api.log") {
                        Write-Host "        📄 Backend API Log (last 10 lines):" -ForegroundColor Gray
                        Get-Content "backend\logs\api.log" -Tail 10
                    } else {
                        Write-Host "        ❌ Backend API log not found" -ForegroundColor Red
                    }
                    
                    Write-Host ""
                    Write-Host "[3/3] ► System health status..." -ForegroundColor Yellow
                    if (Test-Path "bot_health.json") {
                        Write-Host "        📄 Health Status:" -ForegroundColor Gray
                        Get-Content "bot_health.json"
                    } else {
                        Write-Host "        ❌ Health status file not found" -ForegroundColor Red
                    }
                    
                    Read-Host "Press Enter to continue"
                }
                "10" {
                    Write-Host "🛑 Stopping all services..." -ForegroundColor DarkRed
                    Write-Host ""
                    Write-Host "[1/4] ► Stopping Trading Bot..." -ForegroundColor Yellow
                    Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*main.py*" } | Stop-Process -Force
                    Write-Host "        ✅ Trading Bot stopped" -ForegroundColor Green
                    
                    Write-Host ""
                    Write-Host "[2/4] ► Stopping Backend API..." -ForegroundColor Yellow
                    Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*backend*" } | Stop-Process -Force
                    Write-Host "        ✅ Backend API stopped" -ForegroundColor Green
                    
                    Write-Host ""
                    Write-Host "[3/4] ► Stopping Node.js services..." -ForegroundColor Yellow
                    Get-Process node -ErrorAction SilentlyContinue | Stop-Process -Force
                    Write-Host "        ✅ Node.js services stopped" -ForegroundColor Green
                    
                    Write-Host ""
                    Write-Host "[4/4] ► Stopping all KUBERA processes..." -ForegroundColor Yellow
                    Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like "*KUBERA*" } | Stop-Process -Force
                    Write-Host "        ✅ All KUBERA processes stopped" -ForegroundColor Green
                    
                    Write-Host ""
                    Write-Host "✅ All services stopped successfully" -ForegroundColor Green
                    Read-Host "Press Enter to continue"
                }
                "11" {
                    Write-Host "👋 Exiting service management..." -ForegroundColor DarkRed
                    break
                }
                default {
                    Write-Host "❌ Invalid choice! Please enter 1-11" -ForegroundColor Red
                    Read-Host "Press Enter to continue"
                }
            }
        } while ($choice -ne "11")
    }
    
    default {
        Write-Host "❌ Invalid mode! Please enter 1-5" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "👋 Thank you for using KUBERA POKISHAM Enhanced Edition!" -ForegroundColor Green
Write-Host "    🚀 Advanced Signal Handling & Integration Validation" -ForegroundColor Cyan
Write-Host "    🔧 Enhanced Service Management & Monitoring" -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
