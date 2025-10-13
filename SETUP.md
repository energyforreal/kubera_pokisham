# Kubera Pokisham - Setup Guide

Complete setup instructions for the AI Trading Agent MVP.

## Prerequisites

- Python 3.10 or higher
- Delta Exchange API credentials
- Telegram Bot Token
- TA-Lib library

## Step-by-Step Setup

### 1. Install TA-Lib (Required)

#### Windows:
```bash
# Download TA-Lib from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# Install the wheel file
pip install TA_Lib‑0.4.28‑cp310‑cp310‑win_amd64.whl
```

#### Linux/Mac:
```bash
# Install TA-Lib C library
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# Install Python wrapper
pip install TA-Lib
```

### 2. Install Python Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
# Copy template
cp config/env.example .env

# Edit .env file with your credentials
notepad .env  # Windows
nano .env     # Linux/Mac
```

Required variables:
- `DELTA_API_KEY` - Your Delta Exchange API key
- `DELTA_API_SECRET` - Your Delta Exchange API secret
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (from @BotFather)
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID

### 4. Initialize Database

```bash
python scripts/setup_db.py
```

### 5. Download Historical Data

```bash
# Download 1 year of 15-minute data
python scripts/download_data.py --symbol BTCUSDT --timeframe 15m --days 365

# Optional: Download other timeframes
python scripts/download_data.py --symbol BTCUSDT --timeframe 1h --days 365
python scripts/download_data.py --symbol BTCUSDT --timeframe 4h --days 365
```

### 6. Train the Model

```bash
# Train XGBoost model
python scripts/train_model.py --symbol BTCUSDT --timeframe 15m --days 365

# Optional: Run walk-forward validation
python scripts/train_model.py --symbol BTCUSDT --timeframe 15m --days 365 --walk-forward
```

### 7. Run Backtest (Optional)

```bash
# Backtest on historical data
python scripts/backtest.py --data data/BTCUSDT_15m_365d.csv --model models/xgboost_model.pkl
```

### 8. Start Trading Agent

```bash
# Start the main trading loop
python src/main.py
```

## Telegram Bot Commands

Once running, use these commands in Telegram:

- `/start` - Initialize bot
- `/status` - Portfolio status
- `/positions` - Open positions
- `/signals` - Latest AI signals
- `/pause` - Pause trading
- `/resume` - Resume trading
- `/emergency_stop` - Close all positions
- `/daily` - Daily report
- `/help` - Show help

## Testing

```bash
# Run unit tests
pytest tests/test_core.py -v
```

## Configuration

### Risk Management (config/config.yaml)

```yaml
risk_management:
  max_daily_loss_percent: 5        # Max 5% loss per day
  max_drawdown_percent: 15         # Max 15% drawdown
  max_consecutive_losses: 5        # Stop after 5 losses
  stop_loss_atr_multiplier: 2.0    # Stop loss at 2x ATR
  take_profit_risk_reward: 2.0     # 2:1 risk-reward ratio
```

### Position Sizing (config/config.yaml)

```yaml
position_sizing:
  method: "fixed_fractional"       # or "kelly_criterion"
  risk_per_trade: 0.02            # 2% risk per trade
  min_position_size: 100          # Minimum $100
  max_position_size: 2500         # Maximum $2500
```

### Trading Parameters (config/config.yaml)

```yaml
trading:
  symbol: "BTCUSDT"
  initial_balance: 10000.0
  update_interval: 900            # 15 minutes

signal_filters:
  min_confidence: 0.65            # Only trade if >65% confident
```

## Troubleshooting

### TA-Lib Installation Issues

If you get "TA-Lib not found" error:
1. Make sure TA-Lib C library is installed (see step 1)
2. Try: `pip install --no-cache-dir TA-Lib`

### Database Errors

If database errors occur:
1. Delete `kubera_pokisham.db`
2. Run `python scripts/setup_db.py` again

### API Connection Issues

1. Verify API credentials in `.env`
2. Check internet connection
3. Verify Delta Exchange API status

### Model Not Found

If model file not found:
1. Run `python scripts/train_model.py` first
2. Verify model path in `.env` or config.yaml

## File Structure

```
kubera-pokisham/
├── config/               # Configuration files
├── src/                  # Source code
│   ├── core/            # Core utilities
│   ├── data/            # Data pipeline
│   ├── ml/              # ML models
│   ├── risk/            # Risk management
│   ├── trading/         # Trading engine
│   ├── telegram/        # Telegram bot
│   └── main.py          # Main entry point
├── scripts/             # Utility scripts
├── tests/               # Unit tests
├── models/              # Saved models
├── data/                # Historical data
├── logs/                # Log files
└── requirements.txt     # Dependencies
```

## Important Notes

⚠️ **This is for PAPER TRADING ONLY**

- No real money is used
- Simulated trades with realistic execution
- Educational purposes only
- NOT financial advice

## Support

For issues:
1. Check logs in `logs/kubera_pokisham.log`
2. Review error messages in console
3. Verify all configuration settings
4. Ensure all dependencies are installed

## Next Steps

After successful paper trading:
1. Monitor performance for at least 1 month
2. Analyze trade results
3. Optimize parameters
4. Consider live trading only after extensive testing

Good luck! 🚀

