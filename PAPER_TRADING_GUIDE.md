# 📊 Paper Trading Monitoring Guide

## 🚀 Your Trading Bot is Running!

**Status:** Paper Trading Active  
**Model:** xgboost_BTCUSD_15m.pkl (95.25% accuracy)  
**Backtest Results:** 75% win rate, 3.60 profit factor

---

## 📱 Telegram Commands

Use these commands in your Telegram bot to monitor and control trading:

| Command | Description |
|---------|-------------|
| `/status` | Current portfolio status and open positions |
| `/balance` | Account balance and equity |
| `/trades` | Recent trade history |
| `/performance` | Performance metrics (win rate, P&L, etc.) |
| `/pause` | Pause trading (no new positions) |
| `/resume` | Resume trading |
| `/help` | Show all available commands |

---

## 📈 Daily Monitoring Checklist

### **Every Morning (5 minutes):**
- [ ] Check Telegram for overnight notifications
- [ ] Review `/balance` - Check account equity
- [ ] Review `/trades` - See recent trades
- [ ] Check for any risk alerts (circuit breaker triggers)

### **Every Evening (10 minutes):**
- [ ] Run `/performance` - Check win rate and P&L
- [ ] Review the day's signals and trades
- [ ] Note any patterns or observations
- [ ] Check if confidence threshold needs adjustment

### **Weekly Review (30 minutes):**
- [ ] Calculate weekly return %
- [ ] Analyze winning vs losing trades
- [ ] Review trade entry/exit reasons
- [ ] Adjust parameters if needed (see below)

---

## 🔧 Parameter Adjustment Guide

### **Confidence Threshold** (`config/config.yaml`)

**Current Setting:** `min_confidence: 0.65`

**When to Adjust:**

#### Lower to 0.60 (More Trades)
- ✅ If you're getting < 5 trades per week
- ✅ If you want more action to evaluate
- ⚠️ Warning: May decrease win rate slightly

#### Raise to 0.70-0.75 (Higher Quality)
- ✅ If win rate drops below 60%
- ✅ If you're getting too many losing trades
- ⚠️ Warning: Will reduce number of trades

**How to Change:**
```bash
notepad config\config.yaml
```

Find this section:
```yaml
signal_filters:
  min_confidence: 0.65  # Change this value
```

Then restart the bot:
```bash
# Ctrl+C to stop
python src/main.py  # Restart
```

---

## 📊 Key Metrics to Track

### **Performance Targets:**
| Metric | Target | Action if Below |
|--------|--------|-----------------|
| Win Rate | >55% | Increase confidence to 0.70 |
| Profit Factor | >1.5 | Review stop-loss settings |
| Max Drawdown | <10% | Reduce position size |
| Daily P&L | Positive trend | Monitor for 2+ weeks |

### **Risk Management Checks:**
- ✅ No trade should risk more than 2% of balance
- ✅ Daily loss limit: 5% (circuit breaker triggers)
- ✅ Stop-loss always set (2x ATR by default)
- ✅ Take-profit at 2:1 risk-reward ratio

---

## 🎯 What to Look For

### **Good Signs (Keep Going):**
- ✅ Consistent win rate above 55%
- ✅ Profits from winning trades > losses
- ✅ Risk management working correctly
- ✅ No major bugs or errors
- ✅ Telegram notifications arriving on time

### **Warning Signs (Adjust):**
- ⚠️ Win rate dropping below 50%
- ⚠️ Many consecutive losses (>3)
- ⚠️ Circuit breaker triggering frequently
- ⚠️ Signals not aligning with market conditions
- ⚠️ Unusual API errors or data issues

### **Red Flags (Stop and Review):**
- 🚨 Win rate below 40% for 3+ days
- 🚨 Drawdown exceeding 10%
- 🚨 Multiple API failures
- 🚨 Model predictions seem random
- 🚨 Risk management not working

---

## 📝 Daily Log Template

Keep a simple journal to track observations:

```
Date: ___________
Trades Today: ___
Wins/Losses: ___/___ 
Notable Events:
- 
- 
Observations:
- 
- 
Action Items:
- 
```

---

## 🔄 Weekly Optimization Process

### **Week 1-2: Observe Only**
- Don't make changes yet
- Collect data and learn patterns
- Note what works and what doesn't

### **Week 3+: Optimize**
Based on results, consider adjusting:

**1. Confidence Threshold:**
```yaml
# In config/config.yaml
signal_filters:
  min_confidence: 0.70  # Increase for quality, decrease for volume
```

**2. Risk Per Trade:**
```yaml
# In config/config.yaml
position_sizing:
  risk_per_trade: 0.015  # Lower if too volatile (currently 0.02)
```

**3. Stop-Loss Distance:**
```yaml
# In config/config.yaml
risk_management:
  stop_loss_atr_multiplier: 2.5  # Increase if stopped out too often (currently 2.0)
```

---

## 📞 Quick Troubleshooting

### **No Trades Being Executed**
1. Check confidence threshold - may be too high
2. Verify API connection: `/status` command
3. Check logs: `logs/kubera_pokisham.log`
4. Ensure bot is not paused: `/resume`

### **Too Many Losing Trades**
1. Increase confidence: `min_confidence: 0.75`
2. Add multi-timeframe confirmation (use 1h model too)
3. Review market conditions (trending vs ranging)

### **Telegram Not Working**
1. Verify bot token in `.env`
2. Check chat ID is correct
3. Test bot manually: Send `/start` to your bot
4. Check internet connection

### **API Errors**
1. Verify credentials in `.env`
2. Check Delta Exchange API status
3. Ensure sufficient API rate limits
4. Review logs for specific error messages

---

## 🎓 Learning Resources

### **Understanding Signals:**
- **BUY:** Model predicts price will go up
- **SELL:** Model predicts price will go down  
- **HOLD:** No clear direction or low confidence

### **Risk Management Terms:**
- **ATR (Average True Range):** Volatility measure
- **Stop-Loss:** Auto-exit if losing trades goes too far
- **Take-Profit:** Auto-exit when profit target reached
- **Position Size:** Amount risked per trade (2% of balance)
- **Circuit Breaker:** Auto-pause after hitting risk limits

---

## ✅ Success Criteria (Before Going Live)

Before switching to live trading, ensure:

- [ ] Minimum 2 weeks of paper trading
- [ ] Win rate consistently >55%
- [ ] Profit factor >1.5
- [ ] Max drawdown <10%
- [ ] You understand all signals and trades
- [ ] Risk management working correctly
- [ ] No bugs or major issues
- [ ] Comfortable with the bot's behavior

---

## 📅 Paper Trading Timeline

**Weeks 1-2:**
- Focus: Learn and observe
- Goal: Understand bot behavior
- Action: Minimal changes, just watch

**Weeks 3-4:**
- Focus: Optimize parameters
- Goal: Improve performance
- Action: Adjust confidence, risk settings

**Week 5+:**
- Focus: Build confidence
- Goal: Prepare for live trading
- Action: Final validation and testing

---

## 🔐 Safety Reminders

1. ✅ This is PAPER TRADING (no real money yet!)
2. ✅ Review all trades before going live
3. ✅ Never disable risk management
4. ✅ Always use stop-losses
5. ✅ Start live trading with minimal capital
6. ✅ Monitor extremely closely when live
7. ✅ Have an emergency stop plan ready

---

## 📊 Sample Performance Report

Track weekly performance:

```
Week of: Oct 13-20, 2025
=========================
Total Trades: 15
Winning: 11 (73%)
Losing: 4 (27%)
Total P&L: +$124.50 (+1.24%)
Profit Factor: 3.1
Max Drawdown: -3.2%

Best Trade: +$45.20 (BTC long @ 62,150)
Worst Trade: -$18.30 (BTC short @ 63,200)

Notes:
- High win rate maintained
- Model performing well in trending market
- Consider increasing position size to 2.5%

Action: Continue monitoring, no changes needed
```

---

## 🆘 Emergency Stop

If something goes wrong:

1. **Stop the bot immediately:**
   - Press `Ctrl+C` in terminal
   - Or send `/pause` via Telegram

2. **Review logs:**
   ```bash
   notepad logs\kubera_pokisham.log
   ```

3. **Check database:**
   ```bash
   python -c "from src.core.database import SessionLocal; from src.core.database import Trade; db = SessionLocal(); trades = db.query(Trade).all(); print(f'Total trades: {len(trades)}')"
   ```

4. **Contact support or review documentation**

---

**Remember: Paper trading is for learning! Take your time, observe carefully, and only go live when you're 100% confident.**

📈 Happy Trading! 🚀

