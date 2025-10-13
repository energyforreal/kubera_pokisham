# 🚀 Trading Agent - Next Steps Guide

## 📍 Current Status

### ✅ **What's Been Completed:**

1. **ML Models Trained Successfully** (via Google Colab)
   - ✅ XGBoost models for BTCUSD trained on 1 year of data
   - ✅ Models downloaded and installed in `models/` directory
   - ✅ Training completed: Oct 13, 2025

2. **API Integration Fixed**
   - ✅ Updated to Delta Exchange India endpoint (`https://api.india.delta.exchange`)
   - ✅ Correct symbol: `BTCUSD` (not BTCUSDT)
   - ✅ Correct resolution format: string (`15m`, `1h`, `4h`)
   - ✅ All data modules created and pushed to GitHub

3. **Project Structure**
   - ✅ All source code in place (`src/data/`, `src/ml/`, etc.)
   - ✅ Configuration files updated
   - ✅ Google Colab training notebook ready for future retraining

### 📦 **What You Have:**

**Trained Models in `models/` directory:**
```
models/
├── xgboost_BTCUSD_15m.pkl  (555 KB) - 95.25% test accuracy ⭐ BEST
├── xgboost_BTCUSD_1h.pkl   (1.18 MB) - 85.26% test accuracy ✅ GOOD
└── xgboost_BTCUSD_4h.pkl   (1.33 MB) - 30.54% test accuracy ❌ SKIP
```

**Training Results Summary:**
| Timeframe | Train Acc | Val Acc | Test Acc | Samples | Status |
|-----------|-----------|---------|----------|---------|--------|
| 15m | 100% | 98.07% | **95.25%** | 2,654 | ⭐ Production Ready |
| 1h | 100% | 93.16% | **85.26%** | 2,658 | ✅ Use for confirmation |
| 4h | 100% | 33.56% | **30.54%** | 1,390 | ❌ Not usable |

**Recommendation:** Use 15m as primary, 1h for confirmation, skip 4h

---

## 🎯 What To Do Next

### **PHASE 1: Setup & Configuration** (30 minutes)

#### 📝 **Step 1: Create `.env` File**

You need to create a `.env` file with your actual API credentials.

**Commands:**
```bash
# Copy the example file
copy config\env.example .env
```

**Then edit `.env` and add your real credentials:**
```bash
# Delta Exchange API Configuration (India)
DELTA_API_KEY=your_actual_api_key_here
DELTA_API_SECRET=your_actual_api_secret_here
DELTA_API_URL=https://api.india.delta.exchange

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Trading Configuration
INITIAL_BALANCE=10000.0
TRADING_MODE=paper
TRADING_SYMBOL=BTCUSD
```

#### ⚙️ **Step 2: Update `config/config.yaml`**

**Changes needed:**

1. **Point to the best model (15m):**
```yaml
model:
  type: "xgboost"
  path: "models/xgboost_BTCUSD_15m.pkl"  # Changed from generic path
  retrain_interval: 7  # days
```

2. **Remove 4h timeframe (not accurate):**
```yaml
trading:
  symbol: "BTCUSD"
  timeframes:
    - "15m"
    - "1h"
    # - "4h"  # Commented out - only 30% accurate
```

3. **Optional: Adjust confidence threshold if needed:**
```yaml
signal_filters:
  min_confidence: 0.65  # Start here, adjust based on results
```

#### 🧪 **Step 3: Test Models Load Correctly**

Create `test_model.py`:

```python
"""Quick test to verify models work."""
from src.ml.xgboost_model import XGBoostTradingModel

print("🔍 Testing model loading...\n")

# Test 15m model
model_15m = XGBoostTradingModel()
model_15m.load("models/xgboost_BTCUSD_15m.pkl")
print(f"✅ 15m model: {len(model_15m.feature_names)} features")

# Test 1h model  
model_1h = XGBoostTradingModel()
model_1h.load("models/xgboost_BTCUSD_1h.pkl")
print(f"✅ 1h model: {len(model_1h.feature_names)} features")

print("\n🎉 All models loaded successfully!")
```

**Run it:**
```bash
python test_model.py
```

**Expected output:**
```
✅ 15m model: 49 features
✅ 1h model: 49 features
🎉 All models loaded successfully!
```

---

### **PHASE 2: Backtesting** (1-2 hours)

#### 📊 **Step 4: Run Historical Backtest**

Test your model on past data to see how it would have performed:

```bash
python scripts/backtest.py
```

**What to look for in results:**
- ✅ Win rate > 50%
- ✅ Profit factor > 1.5
- ✅ Sharpe ratio > 1.0
- ✅ Max drawdown < 15%
- ✅ Total return positive

**If backtest results are poor:**
- Adjust `min_confidence` in config (try 0.70 or 0.75)
- Review trade logs to understand why losses happened
- Consider using multi-timeframe confirmation

---

### **PHASE 3: Paper Trading** (1-2 weeks minimum)

#### 🗄️ **Step 5: Initialize Database**

```bash
python scripts/setup_db.py
```

This creates the SQLite database for tracking trades and portfolio.

#### 🚀 **Step 6: Start Paper Trading**

```bash
python src/main.py
```

**What happens when you run this:**
1. Connects to Delta Exchange India API
2. Fetches live BTCUSD data every 15 minutes
3. Uses your 15m model to generate predictions
4. Executes paper trades (simulated, no real money)
5. Manages positions with stop-loss and take-profit
6. Sends notifications to Telegram

**Expected console output:**
```
🚀 Kubera Pokisham Trading Agent started!
Trading agent initialized | symbol=BTCUSD interval=900
Fetching market data | symbol=BTCUSD
Getting trading signal
Actionable signal received | prediction=BUY confidence=0.78
```

#### 📱 **Step 7: Monitor via Telegram**

You'll receive notifications for:
- Trade executions (BUY/SELL)
- Position updates
- Stop-loss/Take-profit hits
- Risk alerts (circuit breaker triggers)
- Daily performance reports

**Telegram commands you can use:**
- `/status` - Current portfolio and positions
- `/balance` - Account balance and equity
- `/pause` - Pause trading
- `/resume` - Resume trading
- `/help` - Show all commands

---

### **PHASE 4: Monitoring & Optimization** (Ongoing)

#### 📈 **Step 8: Track Daily Performance**

**Daily checklist:**
- ✅ Check Telegram for trade notifications
- ✅ Review portfolio balance and equity
- ✅ Monitor win rate and profit factor
- ✅ Watch for circuit breaker triggers (risk limits)

**Weekly checklist:**
- ✅ Analyze trading patterns (what works, what doesn't)
- ✅ Check if model accuracy is degrading
- ✅ Review and adjust risk parameters if needed
- ✅ Look for optimization opportunities

#### 🔧 **Step 9: Tune Parameters Based on Results**

**If you're getting too few trades:**
```yaml
signal_filters:
  min_confidence: 0.60  # Lower threshold (was 0.65)
```

**If too many losing trades:**
```yaml
signal_filters:
  min_confidence: 0.75  # Raise threshold (was 0.65)
  require_volume_confirmation: true
```

**If drawdowns are too high:**
```yaml
risk_management:
  max_daily_loss_percent: 3  # Lower (was 5)
  stop_loss_atr_multiplier: 1.5  # Tighter stops (was 2.0)
```

**If you want bigger position sizes:**
```yaml
position_sizing:
  risk_per_trade: 0.03  # Increase (was 0.02) - ONLY if confident
  max_position_size: 5000  # Increase (was 2500)
```

---

### **PHASE 5: Live Trading** (Only after successful paper trading!)

#### ⚠️ **Step 10: Go Live** (ONLY after these criteria are met)

**Required criteria before going live:**
- ✅ Minimum 2 weeks of paper trading
- ✅ Positive returns over the period
- ✅ Win rate consistently > 55%
- ✅ Maximum drawdown < 10%
- ✅ You fully understand all signals and why they trigger
- ✅ Risk management working correctly
- ✅ No major bugs or issues

**How to go live:**

1. **Update `.env` file:**
```bash
TRADING_MODE=live  # Changed from 'paper'
```

2. **Start with reduced risk:**
```yaml
position_sizing:
  risk_per_trade: 0.01  # Half the normal risk initially
```

3. **Start the bot:**
```bash
python src/main.py
```

4. **Monitor extremely closely for the first week!**

---

## 🔄 **Monthly Maintenance**

### **Model Retraining** (Do this monthly)

1. **Go back to Google Colab**
2. **Open `colab_train_models.ipynb`**
3. **Run all cells to retrain with fresh data**
4. **Download new models**
5. **Replace old models in `models/` directory**
6. **Restart the trading bot**

**Why retrain monthly?**
- Market conditions change
- Model accuracy can degrade over time
- New data improves predictions

---

## 📋 **Quick Command Reference**

```bash
# Environment setup
copy config\env.example .env        # Create environment file
notepad .env                         # Edit with your credentials

# Testing
python test_model.py                 # Test model loading
python scripts/backtest.py           # Run historical backtest

# Database
python scripts/setup_db.py           # Initialize database

# Paper trading
python src/main.py                   # Start paper trading bot

# Data management
python scripts/download_data.py      # Download historical data (if needed)

# Retraining
# Use Google Colab notebook: colab_train_models.ipynb
```

---

## 🆘 **Troubleshooting**

### **Issue: Models won't load**
```bash
# Check if files exist
dir models\*.pkl

# Verify paths in config
notepad config\config.yaml

# Test individually
python test_model.py
```

### **Issue: No API data / 400 errors**
```bash
# Verify credentials in .env
notepad .env

# Check API URL is correct
# Must be: https://api.india.delta.exchange

# Test connection
python scripts/download_data.py
```

### **Issue: No trading signals**
```python
# Lower confidence threshold in config/config.yaml
signal_filters:
  min_confidence: 0.55  # Try lower value
```

### **Issue: Too many losing trades**
```python
# Raise confidence threshold
signal_filters:
  min_confidence: 0.75  # Higher = fewer but better trades
```

### **Issue: Telegram not working**
```bash
# Check bot token in .env
# Verify chat ID is correct
# Test bot manually by sending /start
```

### **Issue: ModuleNotFoundError**
```bash
# Install dependencies
pip install -r requirements.txt

# Or install specific package
pip install <package-name>
```

---

## 📊 **Key Performance Metrics to Track**

### **Portfolio Metrics:**
- **Balance** - Cash available
- **Equity** - Balance + unrealized P&L
- **Total P&L** - Overall profit/loss
- **Daily P&L** - Today's profit/loss

### **Trading Metrics:**
- **Win Rate** - % of profitable trades (target: >55%)
- **Profit Factor** - Gross profit / Gross loss (target: >1.5)
- **Sharpe Ratio** - Risk-adjusted returns (target: >1.0)
- **Max Drawdown** - Largest peak-to-trough decline (keep <15%)

### **Risk Metrics:**
- **Position Size** - Should respect risk_per_trade (2%)
- **Stop Loss Distance** - 2x ATR by default
- **Daily Loss Limit** - 5% max by default
- **Consecutive Losses** - Circuit breaker at 5

---

## ⚠️ **Important Safety Reminders**

1. **NEVER skip paper trading** - Test for minimum 2 weeks
2. **Start with small positions** - Even in live trading
3. **Always use stop losses** - Set at 2x ATR minimum
4. **Never risk more than 2% per trade** - Adjust in config
5. **Monitor daily** - Check performance and signals
6. **Keep risk management active** - Don't disable circuit breakers
7. **Retrain models monthly** - Keep them up to date
8. **Have a kill switch ready** - Know how to stop the bot immediately

---

## 🎯 **Your Immediate Action Plan**

### **Today (30 minutes):**
1. ✅ Create `.env` file with your real credentials
2. ✅ Update `config/config.yaml` model path to 15m model
3. ✅ Run `test_model.py` to verify models work
4. ✅ Review and understand the configuration settings

### **Tomorrow (2 hours):**
5. ✅ Run `scripts/backtest.py` to see historical performance
6. ✅ Analyze backtest results and adjust parameters if needed
7. ✅ Run `scripts/setup_db.py` to initialize database
8. ✅ Start paper trading with `python src/main.py`

### **This Week:**
9. ✅ Monitor paper trading daily via Telegram
10. ✅ Track win rate and profit metrics
11. ✅ Adjust confidence threshold based on results
12. ✅ Keep detailed notes on performance

### **Next 2 Weeks:**
13. ✅ Continue paper trading and monitoring
14. ✅ Optimize parameters based on real results
15. ✅ Build confidence in the system
16. ✅ Decide if/when to go live (only if criteria met!)

---

## 📞 **Support & Resources**

**Documentation:**
- `TRAINING_RESULTS_SUMMARY.md` - Detailed training analysis
- `DELTA_API_FIX_SUMMARY.md` - API integration fixes
- `COLAB_TRAINING_GUIDE.md` - How to retrain models
- `README.md` - Project overview
- `SETUP.md` - Initial setup guide

**Key Files:**
- `config/config.yaml` - Main configuration
- `.env` - API credentials (create this!)
- `models/xgboost_BTCUSD_15m.pkl` - Best model
- `src/main.py` - Main trading bot

**GitHub Repository:**
- https://github.com/energyforreal/kubera_pokisham.git

---

## ✅ **Success Checklist**

Before considering live trading, ensure:

- [ ] Paper trading for minimum 2 weeks
- [ ] Win rate consistently above 55%
- [ ] Profit factor above 1.5
- [ ] Maximum drawdown below 10%
- [ ] All risk management working correctly
- [ ] Telegram notifications working
- [ ] You understand all signals
- [ ] You've tested stop-loss and take-profit
- [ ] You've seen the circuit breaker trigger (in testing)
- [ ] You're comfortable with the position sizing
- [ ] You have a plan for when things go wrong
- [ ] You can confidently explain how the bot works

---

## 🚀 **You're Ready!**

**Current Status:** ✅ Models trained and installed
**Next Step:** → Create `.env` file and run `test_model.py`

**Remember:** 
- Start with paper trading (minimum 2 weeks)
- Monitor closely and adjust parameters
- Don't rush to live trading
- The models are good, but need proper risk management!

**Good luck with your trading bot! 📈**

---

*Last Updated: Oct 13, 2025*
*Models Trained: Oct 13, 2025*
*Next Retrain: Nov 13, 2025*

