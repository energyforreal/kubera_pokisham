# ⚡ Quick Reference Card

## 🚀 Starting the Bot

```bash
python src/main.py
```

---

## 🏥 Health Check

```bash
python check_health.py
```

**Expected:**
```
✅ Bot Alive: True
🤖 Models Loaded: 2
⏰ Last Heartbeat: <60s ago
❌ Errors: 0
```

---

## 📱 Telegram Commands

| Command | Purpose |
|---------|---------|
| `/signals` | Multi-model predictions with agreement |
| `/status` | Portfolio & positions |
| `/balance` | Account balance |
| `/performance` | Win rate, profit factor |
| `/help` | All commands |

---

## 📊 Log Monitoring

```bash
# Live logs
Get-Content logs\kubera_pokisham.log -Wait -Tail 20

# Model agreements
Get-Content logs\kubera_pokisham.log | Select-String "AGREEMENT|DISAGREEMENT"

# Errors only
Get-Content logs\kubera_pokisham.log | Select-String "ERROR"

# Performance
Get-Content logs\kubera_pokisham.log | Select-String "duration_ms"
```

---

## 🎯 What to Look For

### Good Signs ✅:
- `Multi-model signal - AGREEMENT`
- `duration_ms` < 1500
- `Errors: 0` in health check
- `Circuit Breaker: Inactive`

### Warning Signs ⚠️:
- `Multi-model signal - DISAGREEMENT` (often = no trades)
- `duration_ms` > 3000 (slow)
- Errors > 5
- No heartbeat in 2+ minutes

---

## 🔧 Quick Fixes

### Restart Bot:
```bash
taskkill /F /IM python.exe
python src/main.py
```

### Check Why No Trades:
```bash
# See if models disagree
Get-Content logs\kubera_pokisham.log | Select-String "DISAGREEMENT"
```

### Adjust Strategy:
Edit `config/config.yaml`:
```yaml
multi_model:
  strategy: "weighted"  # Try weighted or voting for more trades
```

---

## 📈 Performance Metrics

**Target:**
- Signal generation: <1500ms
- Model agreement: >50%
- Win rate: >75%
- Errors per day: 0

**Check:**
- Duration in logs
- Health check file
- Telegram `/performance`

---

## 🆘 Emergency

**Stop Bot:**
```bash
taskkill /F /IM python.exe
```

**Telegram:**
```
/pause
/emergency_stop
```

**Check Status:**
```bash
python check_health.py
```

---

## 📚 Documentation

- `FINAL_STATUS_REPORT.md` - Complete status
- `OPTIMIZATION_SUMMARY.md` - What was fixed
- `MULTI_MODEL_GUIDE.md` - Multi-model usage
- `PAPER_TRADING_GUIDE.md` - Trading guide
- `QUICK_ADJUSTMENTS.md` - Parameter tuning

---

## 💡 Daily Checklist

**Morning:**
- [ ] `python check_health.py`
- [ ] `/status` in Telegram

**Evening:**
- [ ] Check model agreement in logs
- [ ] `/performance` in Telegram

**Weekly:**
- [ ] Review error counts
- [ ] Check performance metrics
- [ ] Analyze trading results

---

**Everything you need on one page! 📋**

