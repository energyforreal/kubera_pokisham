# Kubera Pokisham - AI Trading Agent MVP

An intelligent paper trading agent for Delta Exchange India with ML-based predictions, risk management, and Telegram notifications.

## Features

- 🤖 **XGBoost ML Model** - Predicts BUY/SELL/HOLD signals with confidence scores
- 📊 **Technical Indicators** - 30+ indicators including SMA, EMA, RSI, MACD, ATR, Bollinger Bands
- 🛡️ **Risk Management** - Position sizing, stop loss, take profit, circuit breakers
- 📱 **Telegram Bot** - Real-time alerts and command-based control
- 📈 **Paper Trading** - Realistic simulation with slippage and transaction costs
- 🔄 **Multi-Timeframe** - Analyzes 15m, 1h, and 4h timeframes

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd kubera-pokisham

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp config/env.example .env

# Edit .env with your credentials
# - Delta Exchange API keys
# - Telegram bot token and chat ID
```

### 3. Setup Database

```bash
python scripts/setup_db.py
```

### 4. Download Historical Data

```bash
python scripts/download_data.py --symbol BTCUSDT --days 365
```

### 5. Train Model

```bash
python scripts/train_model.py
```

### 6. Run Backtest

```bash
python scripts/backtest.py
```

### 7. Start Trading

```bash
python src/main.py
```

## Telegram Bot Commands

- `/start` - Initialize bot and show welcome message
- `/status` - View current balance, positions, and PnL
- `/positions` - Detailed information about open positions
- `/signals` - Latest AI prediction with confidence score
- `/pause` - Pause trading (keeps existing positions)
- `/resume` - Resume trading
- `/emergency_stop` - Close all positions immediately
- `/daily` - Daily performance summary

## Project Structure

```
kubera-pokisham/
├── config/          # Configuration files
├── src/             # Source code
│   ├── core/        # Core utilities (config, database, logger)
│   ├── data/        # Data pipeline (API client, features)
│   ├── ml/          # Machine learning (model, training)
│   ├── risk/        # Risk management
│   ├── trading/     # Trading engine
│   └── telegram/    # Telegram bot
├── scripts/         # Utility scripts
├── tests/           # Test files
├── models/          # Saved ML models
├── data/            # Historical data
└── logs/            # Log files
```

## Configuration

Edit `config/config.yaml` to customize:

- Trading parameters (symbol, timeframes, position sizing)
- Risk management (max loss, drawdown limits, stop loss)
- ML model settings (hyperparameters, features)
- Alert preferences

## Risk Management

- **Position Sizing**: 2% risk per trade (configurable)
- **Stop Loss**: 2x ATR (dynamic)
- **Take Profit**: 2:1 risk-reward ratio
- **Circuit Breakers**:
  - 5% daily loss limit
  - 15% max drawdown
  - 5 consecutive losses
  - 5-minute cooldown between trades

## Disclaimer

⚠️ **FOR PAPER TRADING ONLY**

This is an educational project for learning algorithmic trading and machine learning. It is NOT financial advice and should NOT be used for live trading without extensive testing and understanding of the risks involved.

- Past performance does not guarantee future results
- Use at your own risk
- Always paper trade extensively before considering live trading

## License

MIT License - See LICENSE file for details

## Support

For issues and questions, please open a GitHub issue or contact via Telegram.
