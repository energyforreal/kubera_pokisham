@echo off
echo ============================================================
echo     FULL BOT RESTART
echo ============================================================
echo.

echo Step 1: Stopping ALL Python processes...
taskkill /F /IM python.exe /T 2>nul
if %ERRORLEVEL%==0 (
    echo ✓ Stopped existing Python processes
) else (
    echo ✓ No Python processes to stop
)

echo.
echo Step 2: Waiting 3 seconds...
timeout /t 3 /nobreak >nul

echo.
echo Step 3: Starting Trading Bot...
start "Kubera Trading Bot" /MIN python src/main.py

echo.
echo Step 4: Waiting for initialization...
timeout /t 5 /nobreak >nul

echo.
echo Step 5: Checking latest logs...
echo ------------------------------------------------------------
powershell -Command "Get-Content logs\kubera_pokisham.log -Tail 10 | Select-String 'Model loaded|Trading agent initialized|error|Telegram bot started' "

echo.
echo ============================================================
echo ✅ Bot restarted! Check Telegram for confirmation.
echo    - Send /status to verify it's working
echo    - Send /balance to test the model
echo    - Send /help for command list
echo ============================================================
pause

