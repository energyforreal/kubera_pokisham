# ⚡ Quick Start - Trading Agent

## 📍 Status: Models Trained & Ready ✅

**Trained:** Oct 13, 2025  
**Models Location:** `models/` directory  
**Best Model:** `xgboost_BTCUSD_15m.pkl` (95.25% accuracy)

---

## 🚀 Next Steps (30 mins to start)

### 1️⃣ Create `.env` File
```bash
copy config\env.example .env
notepad .env  # Add your real API credentials
```

### 2️⃣ Update Config
Edit `config/config.yaml`:
```yaml
model:
  path: "models/xgboost_BTCUSD_15m.pkl"

timeframes:
  - "15m"
  - "1h"
  # - "4h"  # Skip - only 30% accurate
```

### 3️⃣ Test Models
```bash
python test_model.py
```

### 4️⃣ Run Backtest
```bash
python scripts/backtest.py
```

### 5️⃣ Start Paper Trading
```bash
python scripts/setup_db.py    # Initialize DB
python src/main.py             # Start bot
```

---

## 📊 Model Performance

| Model | Accuracy | Use For |
|-------|----------|---------|
| 15m | **95.25%** | ⭐ Primary trading |
| 1h | **85.26%** | ✅ Confirmation |
| 4h | **30.54%** | ❌ Skip |

---

## 🎯 Current Phase: Paper Trading

**Duration:** Minimum 2 weeks  
**Target Metrics:**
- Win rate > 55%
- Profit factor > 1.5
- Max drawdown < 10%

**Daily Tasks:**
- Check Telegram notifications
- Monitor portfolio balance
- Track win rate

**Weekly Tasks:**
- Analyze performance
- Adjust `min_confidence` if needed
- Review risk parameters

---

## 🔧 Key Settings

**Confidence Threshold:**
- Too few trades? Lower to `0.60`
- Too many losses? Raise to `0.75`

**Risk Management:**
```yaml
risk_per_trade: 0.02         # 2% per trade
max_daily_loss_percent: 5    # 5% daily limit
stop_loss_atr_multiplier: 2.0  # 2x ATR stops
```

---

## 📋 Quick Commands

```bash
# Testing
python test_model.py
python scripts/backtest.py

# Paper Trading
python scripts/setup_db.py
python src/main.py

# Telegram Commands
/status    # Portfolio status
/balance   # Account balance
/pause     # Pause trading
/resume    # Resume trading
```

---

## ⚠️ Important

- ✅ Paper trade for 2+ weeks minimum
- ✅ Use 15m model (95% accuracy)
- ✅ Always use stop losses
- ✅ Max 2% risk per trade
- ✅ Retrain monthly (Google Colab)
- ❌ DON'T skip to live trading
- ❌ DON'T disable risk management

---

## 🆘 Quick Fixes

**No API data?** Check `.env` credentials  
**No signals?** Lower `min_confidence` to `0.60`  
**Too many losses?** Raise `min_confidence` to `0.75`  
**Models won't load?** Check paths in `config.yaml`

---

## 📚 Full Documentation

See `NEXT_STEPS_GUIDE.md` for complete details.

---

**Next Action:** Create `.env` → Test models → Backtest → Paper trade

**Good luck! 📈**

