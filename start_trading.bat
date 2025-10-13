@echo off
echo ============================================================
echo     KUBERA POKISHAM TRADING AGENT
echo ============================================================
echo.
echo Starting paper trading bot...
echo Model: xgboost_BTCUSD_15m.pkl (95.25%% accuracy)
echo Backtest: 75%% win rate, 3.60 profit factor
echo.
echo Press Ctrl+C to stop the bot
echo.
echo ============================================================
echo.

python src/main.py

pause

