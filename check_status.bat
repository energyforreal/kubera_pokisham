@echo off
echo ============================================================
echo     TRADING BOT STATUS CHECK
echo ============================================================
echo.

echo Checking if bot is running...
tasklist /FI "IMAGENAME eq python.exe" 2>NUL | find /I /N "python.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] Python process is running
) else (
    echo [WARNING] No Python process found
)

echo.
echo Latest log entries:
echo ------------------------------------------------------------
powershell -Command "Get-Content logs\kubera_pokisham.log -Tail 5"

echo.
echo ============================================================
echo To view full logs: notepad logs\kubera_pokisham.log
echo To restart bot: restart_bot.bat
echo ============================================================
pause

