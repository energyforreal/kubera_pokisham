@echo off
echo Starting Trading Bot with Safe Signal Handling...
echo.
echo To stop the bot, press Ctrl+C
echo If Ctrl+C doesn't work, close this window or use Task Manager
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Start the safe trading bot
python run_bot_safe.py

echo.
echo Trading Bot has stopped.
pause
