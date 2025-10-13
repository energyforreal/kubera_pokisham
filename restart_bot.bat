@echo off
echo Stopping trading bot...
taskkill /F /IM python.exe /FI "WINDOWTITLE eq *main.py*" 2>nul
timeout /t 2 /nobreak >nul

echo Starting trading bot...
start "Trading Bot" python src/main.py

echo Bot restarted! Check Telegram for confirmation.
pause

