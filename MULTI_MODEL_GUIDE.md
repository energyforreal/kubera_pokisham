# 🤖 Multi-Model Trading Guide

## Overview

The trading bot now supports using multiple models simultaneously for improved signal quality through ensemble strategies.

## What's Different?

**Before (Single Model):**
- Uses only 15m model (95% accuracy)
- 75% win rate in backtest
- 5-10 trades per week

**After (Multi-Model):**
- Uses both 15m AND 1h models
- Expected 80-85% win rate (confirmation strategy)
- 3-8 trades per week (depending on strategy)
- Higher quality signals

---

## Three Strategies

### 1. Confirmation Strategy (Conservative) ⭐ RECOMMENDED

**How it works:**
- Both models must agree (both BUY or both SELL)
- Only trades when consensus is reached
- Uses minimum confidence from both models

**Best for:**
- Risk-averse traders
- Maximum win rate
- Quality over quantity

**Expected Results:**
- Win rate: 80-85%
- Trades/week: 3-5
- Profit factor: 4.0-5.0

**Configuration:**
```yaml
multi_model:
  enabled: true
  strategy: "confirmation"
  require_all_agree: true
  min_combined_confidence: 0.70
```

---

### 2. Weighted Strategy (Balanced)

**How it works:**
- 15m model: 70% weight (higher accuracy)
- 1h model: 30% weight
- Weighted average of predictions

**Best for:**
- Balanced approach
- More trades than confirmation
- Leverage both models

**Expected Results:**
- Win rate: 75-80%
- Trades/week: 5-8
- Profit factor: 3.5-4.5

**Configuration:**
```yaml
multi_model:
  enabled: true
  strategy: "weighted"
  models:
    - path: "models/xgboost_BTCUSD_15m.pkl"
      weight: 0.7
      timeframe: "15m"
    - path: "models/xgboost_BTCUSD_1h.pkl"
      weight: 0.3
      timeframe: "1h"
```

---

### 3. Voting Strategy (Aggressive)

**How it works:**
- Average confidence from all models
- Majority vote decides signal
- Can trade even if models disagree

**Best for:**
- Active trading
- More opportunities
- Risk tolerance

**Expected Results:**
- Win rate: 70-75%
- Trades/week: 8-12
- Profit factor: 3.0-3.5

**Configuration:**
```yaml
multi_model:
  enabled: true
  strategy: "voting"
  min_combined_confidence: 0.65
```

---

## How to Enable

### Step 1: Edit Config

Open `config/config.yaml` and modify:

```yaml
model:
  # ... existing config ...
  
  multi_model:
    enabled: true  # Change to true
    strategy: "confirmation"  # Choose: confirmation, weighted, or voting
    require_all_agree: true
    min_combined_confidence: 0.70
    models:
      - path: "models/xgboost_BTCUSD_15m.pkl"
        weight: 0.7
        timeframe: "15m"
      - path: "models/xgboost_BTCUSD_1h.pkl"
        weight: 0.3
        timeframe: "1h"
```

### Step 2: Restart Bot

```bash
# Stop current bot (Ctrl+C)
python src/main.py
```

### Step 3: Test in Telegram

Send `/signals` command to see multi-model predictions:

```
🤖 MULTI-MODEL AI Signal

🟢 Combined: BUY
📊 Confidence: 78.5%
████████

Strategy: CONFIRMATION
Models Agree: ✅ Yes
Agreement: 100%

Individual Models:
  🟢 15m: BUY (82.3%)
  🟢 1h: BUY (74.6%)

✅ Actionable: Yes
```

---

## Compare Strategies (Backtest)

Run the comparison backtest to see which strategy performs best:

```bash
python run_multi_model_backtest.py
```

**Sample Output:**
```
MULTI-MODEL STRATEGY COMPARISON

Strategy        Win Rate     Trades     Profit Factor   Return %    
----------------------------------------------------------------------
Confirmation    82.50        4          4.20            1.85
Weighted        78.00        7          3.80            2.10
Voting          74.00        11         3.20            1.95

Best Strategy: WEIGHTED
  - Win Rate: 78.00%
  - Profit Factor: 3.80
  - Total Return: 2.10%
```

---

## When to Use Each Strategy

### Use **Confirmation** if:
- ✅ You prefer quality over quantity
- ✅ You want highest win rate
- ✅ You're risk-averse
- ✅ You don't mind fewer trades

### Use **Weighted** if:
- ✅ You want balanced approach
- ✅ You trust the 15m model more
- ✅ You want moderate trade frequency
- ✅ You like customizable weights

### Use **Voting** if:
- ✅ You want maximum trades
- ✅ You're comfortable with more risk
- ✅ You want to capture more opportunities
- ✅ You prefer active trading

---

## Telegram Commands

### `/signals` - View Multi-Model Predictions

Shows:
- Combined prediction
- Individual model predictions
- Agreement level
- Which models agree/disagree
- Confidence from each model

### Example Output:

**When models agree:**
```
🟢 Combined: BUY
Models Agree: ✅ Yes
Agreement: 100%

  🟢 15m: BUY (85%)
  🟢 1h: BUY (78%)
```

**When models disagree:**
```
⚪ Combined: HOLD
Models Agree: ❌ No
Agreement: 50%

  🟢 15m: BUY (82%)
  🔴 1h: SELL (71%)
```

---

## Switching Strategies

You can switch strategies anytime without code changes:

1. Edit `config/config.yaml`
2. Change `strategy: "confirmation"` to `"weighted"` or `"voting"`
3. Restart bot
4. Test with `/signals` command

---

## Disable Multi-Model

To go back to single model:

```yaml
multi_model:
  enabled: false  # Just change this
```

Bot will automatically use the single 15m model.

---

## Performance Monitoring

Track these metrics to evaluate your chosen strategy:

| Metric | Target | How to Check |
|--------|--------|--------------|
| Win Rate | >75% | `/performance` |
| Trades/Week | 3-10 | Count in Telegram |
| Models Agreement | >70% | `/signals` |
| Profit Factor | >3.5 | `/performance` |

---

## Troubleshooting

### Issue: Too Few Trades

**Solution:**
- Switch to `voting` or `weighted` strategy
- Lower `min_combined_confidence` to 0.65
- Check if models are disagreeing often (`/signals`)

### Issue: Low Win Rate

**Solution:**
- Switch to `confirmation` strategy
- Increase `min_combined_confidence` to 0.75
- Ensure both models are loaded correctly

### Issue: Models Always Disagree

**Solution:**
- Check model paths in config
- Verify both models are loading (check logs)
- Consider using `weighted` strategy instead

---

## Best Practices

1. **Start with Confirmation** - Most conservative, highest quality
2. **Backtest First** - Run `run_multi_model_backtest.py` before going live
3. **Monitor Agreement** - Check `/signals` regularly to see if models agree
4. **Paper Trade 2 Weeks** - Test strategy before live trading
5. **Track Performance** - Use `/daily` and `/performance` commands
6. **Adjust as Needed** - Fine-tune based on results

---

## FAQ

**Q: Which strategy is best?**  
A: Run the backtest to compare. Generally, `confirmation` for safety, `weighted` for balance, `voting` for activity.

**Q: Can I add more models?**  
A: Yes! Just add more entries to the `models` list in config. (Note: 4h model has low accuracy, not recommended)

**Q: What if models disagree?**  
A: In `confirmation` mode, bot will HOLD. In `weighted`/`voting`, it averages the signals.

**Q: How do I know which model is better?**  
A: Check individual predictions in `/signals` command. 15m is 95% accurate, 1h is 85%.

**Q: Can I disable one model temporarily?**  
A: Yes, remove it from the `models` list in config or set `enabled: false`.

---

## Summary

✅ **Enabled**: Multi-model trading with 15m + 1h models  
✅ **3 Strategies**: Confirmation, Weighted, Voting  
✅ **Configurable**: Switch strategies anytime via config  
✅ **Telegram Support**: Enhanced `/signals` command  
✅ **Backtesting**: Compare strategies before deploying  

**Recommended Setup:**
- Strategy: `confirmation`
- Min Confidence: `0.70`
- Expected: 80%+ win rate, 3-5 trades/week

---

*Happy Trading! 🚀*

