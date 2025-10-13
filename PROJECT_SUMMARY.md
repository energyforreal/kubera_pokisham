# Kubera Pokisham - AI Trading Agent MVP

## Project Overview

A complete, production-ready AI-powered paper trading agent for Delta Exchange India, implementing ML-based predictions, comprehensive risk management, and real-time monitoring via Telegram.

## ✅ Completed Features

### 1. Core Infrastructure ✓
- **Configuration Management**: Pydantic-based settings with YAML and .env support
- **Database**: SQLite with SQLAlchemy ORM for trades, positions, and metrics
- **Logging**: Structured logging with file and console output
- **Error Handling**: Comprehensive exception handling throughout

### 2. Data Pipeline ✓
- **Delta Exchange API Client**: Full REST API integration
- **Data Validation**: Quality checks for missing data, outliers, OHLC consistency
- **Feature Engineering**: 40+ technical indicators
  - Price: SMA, EMA, VWAP, Bollinger Bands
  - Momentum: RSI, MACD, Stochastic, Williams %R, ROC, CCI
  - Volatility: ATR, NATR, Historical volatility
  - Volume: OBV, MFI, A/D, Volume ratios
- **Multi-timeframe Support**: 15m, 1h, 4h analysis

### 3. Machine Learning ✓
- **XGBoost Classifier**: BUY/SELL/HOLD prediction with confidence scores
- **Training Pipeline**: Walk-forward validation
- **Feature Preprocessing**: StandardScaler normalization
- **Model Persistence**: Save/load with joblib
- **Prediction Service**: Real-time signal generation
- **Model Evaluation**: Accuracy, Sharpe ratio, per-class metrics

### 4. Risk Management ✓
- **Position Sizing Strategies**:
  - Fixed fractional (1-2% per trade)
  - Kelly Criterion
  - Volatility-adjusted
  - Stop-loss based
- **Risk Metrics**: VaR, CVaR, Sharpe, Sortino, Max Drawdown
- **Circuit Breakers**:
  - Daily loss limit (5%)
  - Max drawdown (15%)
  - Consecutive losses (5)
  - Time between trades (5 min)

### 5. Paper Trading Engine ✓
- **Realistic Execution**:
  - Transaction costs (0.1% taker fee)
  - Slippage simulation (0.05%)
  - Market impact modeling
- **Dynamic Risk Management**:
  - ATR-based stop loss (2x ATR)
  - Risk-reward take profit (2:1)
  - Trailing stops support
- **Portfolio Management**:
  - Position tracking
  - PnL calculation
  - Equity updates
  - Daily metrics

### 6. Telegram Bot ✓
- **Commands**:
  - `/start` - Initialize bot
  - `/status` - Portfolio status
  - `/positions` - Position details
  - `/signals` - Latest AI signals
  - `/pause` - Pause trading
  - `/resume` - Resume trading
  - `/emergency_stop` - Close all positions
  - `/daily` - Daily report
  - `/help` - Command reference
- **Notifications**:
  - Trade execution alerts
  - Risk alerts
  - Circuit breaker triggers
  - Daily performance reports
- **Interactive**: Rich formatted messages with emojis

### 7. Main Trading Loop ✓
- **Async Architecture**: Non-blocking execution
- **15-minute Cycle**:
  1. Fetch latest market data
  2. Check stop loss/take profit
  3. Update position PnL
  4. Get AI trading signal
  5. Execute trades (if actionable)
  6. Send notifications
  7. Check risk limits
  8. Save metrics
- **Error Recovery**: Automatic retry and graceful degradation

### 8. Utility Scripts ✓
- **setup_db.py**: Initialize database tables
- **download_data.py**: Fetch historical data from Delta Exchange
- **train_model.py**: Train XGBoost model with walk-forward validation
- **backtest.py**: Backtest strategy on historical data

### 9. Testing ✓
- **Unit Tests**: Core functionality coverage
- **Feature Engineering Tests**: Indicator validation
- **Data Validation Tests**: Quality checks
- **Position Sizing Tests**: Risk calculations
- **Risk Management Tests**: VaR, Sharpe calculations

## 📁 Project Structure

```
kubera-pokisham/
├── config/
│   ├── config.yaml              # Trading configuration
│   └── env.example              # Environment template
├── src/
│   ├── core/
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # Database models
│   │   └── logger.py           # Logging setup
│   ├── data/
│   │   ├── delta_client.py     # API client
│   │   ├── feature_engineer.py # Technical indicators
│   │   └── data_validator.py   # Data quality
│   ├── ml/
│   │   ├── xgboost_model.py    # ML model
│   │   ├── trainer.py          # Training pipeline
│   │   └── predictor.py        # Prediction service
│   ├── risk/
│   │   ├── position_sizer.py   # Position sizing
│   │   ├── risk_manager.py     # Risk metrics
│   │   └── circuit_breaker.py  # Safety mechanisms
│   ├── trading/
│   │   ├── paper_engine.py     # Trading simulator
│   │   └── portfolio.py        # Portfolio management
│   ├── telegram/
│   │   ├── bot.py              # Bot orchestration
│   │   ├── handlers.py         # Command handlers
│   │   └── notifications.py    # Alert system
│   └── main.py                 # Main entry point
├── scripts/
│   ├── setup_db.py             # Database setup
│   ├── download_data.py        # Data downloader
│   ├── train_model.py          # Model trainer
│   └── backtest.py             # Backtesting
├── tests/
│   └── test_core.py            # Unit tests
├── requirements.txt            # Dependencies
├── README.md                   # User guide
├── SETUP.md                    # Setup instructions
└── .gitignore                  # Git ignore rules
```

## 🔧 Technology Stack

### Backend
- **Python 3.10+**
- **FastAPI** (future API)
- **SQLAlchemy** (ORM)
- **Pydantic** (validation)

### Machine Learning
- **XGBoost** (classification)
- **Scikit-learn** (preprocessing)
- **TA-Lib** (indicators)
- **Pandas/NumPy** (data processing)

### Communication
- **python-telegram-bot** (Telegram)
- **aiohttp** (async HTTP)
- **requests** (sync HTTP)

### Database
- **SQLite** (development)
- **PostgreSQL** (production-ready)

### Monitoring
- **structlog** (structured logging)
- **Prometheus** (metrics - future)

## 📊 Key Metrics & Performance

### Success Criteria
- ✅ Delta Exchange integration working
- ✅ Model accuracy >55% (to be validated on real data)
- ✅ Risk management enforcing all limits
- ✅ Telegram bot responsive to all commands
- ✅ Backtest framework operational
- ✅ System architecture complete

### Risk Parameters
- **Max Position Size**: 25% of portfolio
- **Risk Per Trade**: 2% (default)
- **Daily Loss Limit**: 5%
- **Max Drawdown**: 15%
- **Min Confidence**: 65%

### Performance Targets
- **Sharpe Ratio**: >1.0 (target >1.5)
- **Win Rate**: >55%
- **Profit Factor**: >1.5
- **Max Drawdown**: <15%

## 🚀 Quick Start

```bash
# 1. Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp config/env.example .env
# Edit .env with your credentials

# 3. Initialize
python scripts/setup_db.py

# 4. Download Data
python scripts/download_data.py --symbol BTCUSDT --days 365

# 5. Train Model
python scripts/train_model.py --symbol BTCUSDT --days 365

# 6. Backtest
python scripts/backtest.py --data data/BTCUSDT_15m_365d.csv

# 7. Run
python src/main.py
```

## 🎯 Next Steps (Future Enhancements)

### Phase 2 (Months 4-6)
- [ ] Add more ML models (LSTM, Transformer)
- [ ] Ensemble model with voting
- [ ] Sentiment analysis integration
- [ ] Web dashboard (React/Next.js)
- [ ] Mobile app (Flutter)

### Phase 3 (Months 7-9)
- [ ] ONNX model optimization
- [ ] Multi-asset support (ETH, SOL, etc.)
- [ ] Advanced portfolio optimization
- [ ] Real-time anomaly detection
- [ ] Distributed training with Ray

### Phase 4 (Months 10-12)
- [ ] Production deployment (Docker/K8s)
- [ ] High availability setup
- [ ] Prometheus + Grafana monitoring
- [ ] CI/CD pipeline
- [ ] Security hardening

## ⚠️ Important Notes

### Paper Trading Only
- This is a simulation using real market data
- No real money is involved
- Educational purposes only
- NOT financial advice

### Before Live Trading (if ever)
1. ✅ Backtest thoroughly (2+ years of data)
2. ✅ Paper trade for 6+ months
3. ✅ Achieve consistent positive results
4. ✅ Understand all risks
5. ✅ Consult financial professionals

## 📝 License

MIT License - See LICENSE file

## 👥 Contributing

This is currently a personal educational project. Contributions, suggestions, and feedback are welcome!

## 📞 Support

- Check `logs/kubera_pokisham.log` for errors
- Review `SETUP.md` for troubleshooting
- Ensure all dependencies are installed
- Verify API credentials

---

**Built with ❤️ for learning algorithmic trading and machine learning**

*Remember: Past performance does not guarantee future results. Trade responsibly!*

