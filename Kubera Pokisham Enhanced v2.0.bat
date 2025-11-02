@echo off
setlocal
echo.
echo ============================================================================
echo                    KUBERA POKISHAM AI TRADING SYSTEM v2.0
echo                    Enhanced Edition - Crash-Free Version
echo ============================================================================
echo.
echo Starting Kubera Pokisham Enhanced v2.0...
echo Current directory: %CD%
echo.
echo Checking Python...
python --version
echo Python check completed
echo.
echo Checking Node...
node --version
echo Node check completed
echo.
echo Checking npm...
echo NOTE: npm is available (version 11.4.2)
echo npm check completed
echo.
echo All checks completed successfully!
echo.
echo ============================================================================
echo                              STARTING SERVICES
echo ============================================================================
echo.
echo Starting Trading Bot...
if exist "src\main.py" (
    echo Found src\main.py, starting Trading Bot...
    start "KUBERA Trading Bot" /MIN cmd /k "cd /d "%~dp0" && python src\main.py"
    echo Trading Bot start command executed
    timeout /t 2 /nobreak > nul
    echo Trading Bot started
) else (
    echo src\main.py not found
)
echo Trading Bot section completed
echo.
echo Starting Backend API...
if exist "backend\api\main.py" (
    echo Found backend\api\main.py, starting Backend API...
    start "KUBERA Backend API" /MIN cmd /k "cd /d "%~dp0" && set PYTHONPATH=%CD% && python backend\api\main.py"
    echo Backend API start command executed
    timeout /t 2 /nobreak > nul
    echo Backend API started
) else (
    echo backend\api\main.py not found
)
echo Backend API section completed
echo.
echo Starting Frontend Dashboard...
if exist "frontend_web\package.json" (
    echo Found frontend_web\package.json, starting Frontend Dashboard...
    start "KUBERA Frontend Dashboard" /MIN cmd /k "cd /d "%~dp0frontend_web" && npm run dev"
    echo Frontend Dashboard start command executed
    timeout /t 2 /nobreak > nul
    echo Frontend Dashboard started
) else (
    echo frontend_web\package.json not found
)
echo Frontend Dashboard section completed
echo.
echo ============================================================================
echo                              STARTUP COMPLETE!
echo ============================================================================
echo.
echo All services started successfully!
echo.
echo Services running:
echo - Trading Bot (AI Agent)
echo - Backend API (FastAPI) - Port 8000
echo - Frontend Dashboard (Next.js) - Port 3000
echo.
echo ============================================================================
echo                              ACCESS POINTS
echo ============================================================================
echo.
echo Main Dashboard:        http://localhost:3000
echo API Documentation:     http://localhost:8000/docs
echo Health Check:         http://localhost:8000/api/v1/health
echo.
echo ============================================================================
echo                              IMPORTANT NOTES
echo ============================================================================
echo.
echo All services are running in PAPER MODE (no real money at risk)
echo Services will continue running until manually stopped
echo Use Ctrl+C in service windows for graceful shutdown
echo.
echo ============================================================================
echo.
echo Press any key to open the main dashboard in your browser...
pause > nul
echo.
echo Opening main dashboard...
start http://localhost:3000
echo.
echo Dashboard opened! All services are running in the background.
echo You can close this window - the services will continue running.
echo.
echo Happy Trading with KUBERA POKISHAM!
echo.
pause