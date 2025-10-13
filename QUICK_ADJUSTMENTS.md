# ⚡ Quick Parameter Adjustments

## 🎯 Confidence Threshold Tuning

**File:** `config/config.yaml`  
**Section:** `signal_filters` → `min_confidence`

### Current Setting: 0.65

| Setting | Trades/Week | Win Rate | Use When |
|---------|-------------|----------|----------|
| **0.55** | 20-30 | ~65% | Want maximum trades |
| **0.60** | 15-25 | ~70% | Want more action |
| **0.65** | 10-15 | ~75% | **CURRENT - Balanced** |
| **0.70** | 5-10 | ~80% | Want quality over quantity |
| **0.75** | 3-8 | ~85% | Only high-confidence trades |
| **0.80** | 1-5 | ~90% | Ultra-conservative |

### How to Change:

```bash
notepad config\config.yaml
```

Find and edit:
```yaml
signal_filters:
  min_confidence: 0.65  # Change this number
```

**Restart bot after changing:**
```bash
Ctrl+C  # Stop current bot
python src/main.py  # Restart
```

---

## 💰 Risk Adjustments

### Position Size (Risk Per Trade)

**Default:** 2% per trade  
**File:** `config/config.yaml` → `position_sizing` → `risk_per_trade`

```yaml
position_sizing:
  risk_per_trade: 0.02  # Options: 0.01 (conservative) to 0.03 (aggressive)
```

| Value | Risk Level | Recommended For |
|-------|------------|-----------------|
| 0.01 | Very Conservative | Live trading start |
| 0.015 | Conservative | Paper trading, cautious |
| 0.02 | **Balanced (Current)** | Standard paper trading |
| 0.025 | Aggressive | High confidence only |
| 0.03 | Very Aggressive | Expert traders only |

---

### Stop-Loss Distance

**Default:** 2.0x ATR  
**File:** `config/config.yaml` → `risk_management` → `stop_loss_atr_multiplier`

```yaml
risk_management:
  stop_loss_atr_multiplier: 2.0  # Tighter = 1.5, Wider = 2.5-3.0
```

| Value | Description | Effect |
|-------|-------------|--------|
| 1.5 | Tight stops | More stop-outs, lower losses |
| 2.0 | **Standard (Current)** | Balanced |
| 2.5 | Wider stops | Fewer stop-outs, bigger losses |
| 3.0 | Very wide | Let trades breathe, risky |

---

## 📊 Common Scenarios

### "Not Enough Trades"
```yaml
signal_filters:
  min_confidence: 0.60  # Lower from 0.65
```

### "Too Many Losses"
```yaml
signal_filters:
  min_confidence: 0.75  # Raise from 0.65
```

### "Getting Stopped Out Too Often"
```yaml
risk_management:
  stop_loss_atr_multiplier: 2.5  # Increase from 2.0
```

### "Drawdown Too High"
```yaml
position_sizing:
  risk_per_trade: 0.015  # Lower from 0.02
risk_management:
  max_daily_loss_percent: 3  # Lower from 5
```

---

## 🔄 Multi-Timeframe Confirmation (Advanced)

To require both 15m and 1h models to agree before trading:

**1. Load both models in your code**
**2. Modify trading logic to check both signals**

This reduces trades but increases quality significantly.

---

## ⏱️ Trading Hours (Optional)

If you want to trade only during specific hours, add to `config.yaml`:

```yaml
trading_hours:
  enabled: true
  start_hour: 8  # 8 AM UTC
  end_hour: 20   # 8 PM UTC
  timezone: "UTC"
```

---

## 🎯 Recommended Starting Configuration

For first 2 weeks of paper trading:

```yaml
signal_filters:
  min_confidence: 0.65  # Balanced

position_sizing:
  risk_per_trade: 0.02  # Standard

risk_management:
  stop_loss_atr_multiplier: 2.0  # Balanced
  take_profit_risk_reward: 2.0  # 2:1 RR
  max_daily_loss_percent: 5     # Conservative daily limit
```

**Don't change these until you have 1-2 weeks of data!**

---

## 📝 Change Log Template

Keep track of your changes:

```
Date: ___________
Change: min_confidence 0.65 → 0.70
Reason: Too many losing trades
Expected: Fewer trades, higher win rate
Result (after 3 days): _______________
```

---

## ⚠️ Important Notes

1. **Change ONE thing at a time** - Wait 3-7 days before changing again
2. **Document every change** - Keep a log
3. **Never disable risk management** - Always use stop-losses
4. **Backtest changes first** - Run `python run_backtest.py` with new settings
5. **Be patient** - Good trading strategies need time to prove themselves

---

**Current Status:** Ready for paper trading with balanced settings ✅

