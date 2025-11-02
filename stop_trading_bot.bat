@echo off
echo Stopping Trading Bot...
echo.

REM Find Python processes running trading bot
echo Searching for trading bot processes...

REM Method 1: Find by command line
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr /i "main.py"') do (
    echo Found trading bot process: %%i
    taskkill /PID %%i /F
    echo Killed process %%i
)

REM Method 2: Find by window title (if any)
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr /i "trading"') do (
    echo Found trading process: %%i
    taskkill /PID %%i /F
    echo Killed process %%i
)

REM Method 3: Kill all Python processes (use with caution)
if "%1"=="--force" (
    echo Force killing all Python processes...
    taskkill /IM python.exe /F
    echo All Python processes killed
) else (
    echo To force kill all Python processes, run: stop_trading_bot.bat --force
)

echo.
echo Trading bot stop complete.
pause
