# 🚀 .BAT Files Guide - Which One to Use?

## 📌 Quick Answer

### 🎯 **Want Everything? (Trading + Dashboard)**
```batch
start_EVERYTHING.bat
```
**This starts:**
1. ✅ Trading Bot (does actual trading)
2. ✅ Backend API (powers dashboard)
3. ✅ Frontend Dashboard (web UI)

**Use this for:** Full system with trading and web interface

---

### 📊 **Want Dashboard Only? (No Trading)**
```batch
start_DASHBOARD_ONLY.bat
```
**This starts:**
1. ✅ Backend API
2. ✅ Frontend Dashboard

**Does NOT start:** Trading bot

**Use this for:** Just viewing the dashboard UI without active trading

---

### 🤖 **Want Trading Only? (No Dashboard)**
```batch
start_bot.bat
```
**This starts:**
1. ✅ Trading Bot only

**Does NOT start:** Dashboard or API

**Use this for:** Headless trading with Telegram notifications

---

## 📋 All Available .BAT Files

### ✅ MAIN FILES (Use These)

| File | What It Does | When to Use |
|------|--------------|-------------|
| **start_EVERYTHING.bat** | Trading Bot + Backend + Dashboard | Want full system |
| **start_DASHBOARD_ONLY.bat** | Backend + Dashboard (no trading) | Just view dashboard |
| **start_bot.bat** | Trading Bot only | Trading without dashboard |

### 🛠️ UTILITY FILES

| File | What It Does |
|------|--------------|
| **stop_all.bat** | Stop all running services |
| **check_status.bat** | Check if services are running |
| **restart.bat** | Restart all services |

### ❌ REMOVED (Had Errors)
- ~~start_dashboard.bat~~ - Deleted (had import errors)
- ~~start_dashboard_fixed.bat~~ - Deleted (had import errors)
- ~~start_backend_only.bat~~ - Deleted (had import errors)
- ~~test_backend.bat~~ - Deleted (not needed)

---

## 🎯 What Each Component Does

### 1. **Trading Bot** (`src/main.py`)
- Fetches market data
- Runs ML predictions
- Executes trades (paper trading)
- Manages positions
- Risk management
- Telegram notifications

### 2. **Backend API** (`backend/api/main.py`)
- REST API for dashboard
- WebSocket for live updates
- Endpoints for trades, positions, analytics
- Separate from trading bot

### 3. **Frontend Dashboard** (`frontend_web/`)
- Web UI at http://localhost:3000
- Real-time charts
- Position management
- Trade execution interface
- Analytics and performance metrics

---

## 💡 Common Scenarios

### Scenario 1: "I want to trade AND see the dashboard"
```batch
start_EVERYTHING.bat
```

### Scenario 2: "I just want to test the dashboard UI"
```batch
start_DASHBOARD_ONLY.bat
```

### Scenario 3: "I want trading but no web UI (Telegram only)"
```batch
start_bot.bat
```

### Scenario 4: "Everything is running, I want to stop it"
```batch
stop_all.bat
```

---

## ✅ Recommended Workflow

**First Time:**
1. Run: `start_EVERYTHING.bat`
2. Wait 30 seconds
3. Open: http://localhost:3000
4. Test all features
5. Stop with: `stop_all.bat`

**Daily Use:**
- Active trading + monitoring: `start_EVERYTHING.bat`
- Just checking dashboard: `start_DASHBOARD_ONLY.bat`
- Headless trading: `start_bot.bat`

---

## 🔍 Verification

After running `start_EVERYTHING.bat`, you should see:

**Three windows open (minimized):**
1. KUBERA Trading Bot
2. Trading API Backend
3. Trading Dashboard

**In browser at localhost:3000:**
- ✅ Green "Live" indicator
- ✅ Symbol prices loading
- ✅ No console errors
- ✅ WebSocket connected
- ✅ Portfolio metrics showing

**In backend window:**
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**In bot window:**
```
[INFO] Trading bot initialized
[INFO] Multi-model predictor loaded
[INFO] Paper trading mode active
```

---

## ⚙️ What Was Fixed

1. ✅ **Frontend Hydration Error** - Fixed `SymbolSelector.tsx`
2. ✅ **Backend Import Errors** - Fixed Python path in new .bat files
3. ✅ **Module Dependencies** - All packages installed
4. ✅ **Startup Scripts** - Created working versions

---

## 🎉 Summary

**Use:** `start_EVERYTHING.bat` for full functionality

**This gives you:**
- ✅ Active paper trading
- ✅ ML predictions
- ✅ Web dashboard
- ✅ Real-time monitoring
- ✅ All features working

**Access:** http://localhost:3000 after 30 seconds

---

**Questions?** Check `EXECUTE_THIS.txt` or `SIMPLE_START_GUIDE.md`

