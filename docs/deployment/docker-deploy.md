# 🚀 How to Deploy the Trading Agent

## Quick Start (No Batch Files Needed!)

### Method 1: Direct Python Command (EASIEST)
```bash
python src/main.py
```

### Method 2: PowerShell with Output Buffering
```powershell
$env:PYTHONUNBUFFERED=1
python src/main.py
```

### Method 3: Background Process
```powershell
Start-Process python -ArgumentList "src/main.py" -NoNewWindow
```

### Method 4: With Logging
```bash
python src/main.py > logs/agent_output.log 2>&1
```

---

## Before You Start

### 1. Configure API Keys
Create `config/.env` from `config/env.example`:

```env
# Delta Exchange API (Required)
DELTA_API_KEY=your_api_key_here
DELTA_API_SECRET=your_api_secret_here

# Telegram Bot (Optional)
TELEGRAM_BOT_TOKEN=your_token_here
```

### 2. Verify Configuration
```bash
python test_new_models.py
```

Should show: `✅ All tests passed!`

---

## Starting the Agent

### Step-by-Step:

1. **Open PowerShell/Terminal** in the project directory

2. **Run the agent:**
   ```bash
   python src/main.py
   ```

3. **You should see:**
   ```
   Loading model from models/randomforest_BTCUSD_4h...
   Loaded raw model
   Loading model from models/xgboost_BTCUSD_4h...
   Loaded wrapped model
   🚀 Kubera Pokisham Trading Agent started!
   Trading loop started
   ```

4. **Monitor logs:**
   - Check `logs/kubera_pokisham.log`
   - Watch for trade signals every 4 hours

5. **Stop the agent:**
   - Press `Ctrl+C` in the terminal

---

## Troubleshooting

### "No module named 'src'"
```bash
# Make sure you're in the project root
cd "C:\Users\lohit\OneDrive\Documents\ATTRAL\Projects\Trading Agent"
python src/main.py
```

### "Module not found"
```bash
# Install requirements
pip install -r requirements.txt
```

### "Model file not found"
```bash
# Verify models exist
dir models\*production*.pkl
```

### "API Error"
- Check your Delta Exchange API keys in `config/.env`
- Ensure keys have trading permissions
- Verify internet connection

---

## Monitoring

### View Live Logs
```powershell
Get-Content logs\kubera_pokisham.log -Wait -Tail 20
```

### Check Recent Trades
```bash
python -c "from src.core.database import SessionLocal, Trade; db = SessionLocal(); trades = db.query(Trade).all()[-5:]; [print(f'{t.timestamp}: {t.signal} @ ${t.entry_price}') for t in trades]"
```

### Test Models
```bash
python test_new_models.py
```

---

## What to Expect

### First Run
- Models load (2-3 seconds)
- Database initializes
- Telegram bot connects (if configured)
- Trading loop starts

### During Operation
- Checks market every 4 hours
- Generates predictions from 2 models
- Executes trades if confidence > 60%
- Logs all activity

### Performance
- **Paper Trading Mode** - No real money at risk
- **Risk Limited** - Max 2% per trade, 5% daily loss
- **Stop Loss Active** - Automatic at 2x ATR
- **Circuit Breaker** - Stops after 5 consecutive losses

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python src/main.py` | Start the agent |
| `python test_new_models.py` | Test models |
| `Ctrl+C` | Stop the agent |
| `type logs\kubera_pokisham.log` | View logs |
| `dir models\*.pkl` | List models |

---

## Need Help?

1. **Check logs:** `logs/kubera_pokisham.log`
2. **Run tests:** `python test_new_models.py`
3. **Review docs:**
   - `DEPLOYMENT_STATUS.md` - Full guide
   - `MODEL_INTEGRATION_COMPLETE.md` - Technical details
   - `QUICK_START_PRODUCTION_MODELS.md` - Quick start

---

## Ready to Deploy? ✅

1. Configure API keys in `config/.env`
2. Run: `python src/main.py`
3. Monitor: `logs/kubera_pokisham.log`
4. Track performance for 6+ months before going live!

**Happy Trading! 📈🚀**

