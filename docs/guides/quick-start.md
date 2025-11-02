# 🚀 Quick Start Guide - Kubera Pokisham Trading Agent

## Available Commands

### 1. **Start Trading Bot Only**
```bash
start_bot.bat
```
- Starts the trading bot with Telegram integration
- Paper trading mode (safe testing)
- No web dashboard

**When to use:** You only want the bot running and interacting via Telegram

---

### 2. **Start Dashboard Only**
```bash
start_dashboard.bat
```
- Starts Backend API (port 8000)
- Starts Frontend Dashboard (port 3000)
- Access at: http://localhost:3000

**When to use:** You want to monitor and interact through the web interface

---

### 3. **Start Everything** ⭐ Recommended
```bash
start_all.bat
```
- Starts Trading Bot
- Starts Backend API
- Starts Frontend Dashboard
- Full system with all features

**When to use:** You want complete access via Telegram AND web dashboard

---

### 4. **Restart Everything**
```bash
restart.bat
```
- Stops all running services
- Restarts Trading Bot + API + Dashboard
- Shows health check logs

**When to use:** System is running but not responding, or you want a fresh start

---

### 5. **Stop All Services**
```bash
stop_all.bat
```
- Stops all Python processes (Bot + API)
- Stops all Node.js processes (Dashboard)

**When to use:** End of trading session, shutting down

---

## 📋 Typical Workflows

### First Time Setup
1. Install dependencies (one time):
   ```bash
   pip install -r requirements.txt
   cd frontend_web && npm install && cd ..
   ```

2. Start everything:
   ```bash
   start_all.bat
   ```

3. Verify:
   - Send `/status` to Telegram bot
   - Open http://localhost:3000 in browser

### Daily Trading
```bash
# Morning - Start system
start_all.bat

# During trading - Monitor both:
# - Telegram for notifications
# - Dashboard for real-time charts

# Evening - Stop system
stop_all.bat
```

### Bot Only (Lightweight)
```bash
# If you don't need the dashboard
start_bot.bat

# Control via Telegram
# /status, /balance, /portfolio, etc.
```

### Dashboard Only (Monitoring)
```bash
# If you just want to monitor existing positions
start_dashboard.bat
```

---

## 🔗 Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| **Dashboard** | http://localhost:3000 | Main web interface |
| **API Docs** | http://localhost:8000/docs | Backend API documentation |
| **Telegram Bot** | Your Telegram app | Send `/help` for commands |

---

## ⚠️ Troubleshooting

**Bot not responding?**
```bash
restart.bat
```

**Port already in use?**
- Check if services are already running
- Use `stop_all.bat` first, then start again

**Dashboard won't load?**
- Ensure Backend API is running (http://localhost:8000/docs should work)
- Check frontend_web dependencies: `cd frontend_web && npm install`

**Logs not showing?**
- Check `logs/kubera_pokisham.log` for detailed information

---

## 📂 File Structure

```
Trading Agent/
├── start_bot.bat          # Start trading bot only
├── start_dashboard.bat    # Start web dashboard only
├── start_all.bat         # Start everything
├── restart.bat           # Full system restart
├── stop_all.bat          # Stop all services
├── src/                  # Trading bot source
├── backend/              # API backend
├── frontend_web/         # Web dashboard
└── logs/                 # Log files
```

---

## 🎯 Recommended: Use `start_all.bat`

For the best experience, use **`start_all.bat`** to get:
- ✅ Telegram notifications and control
- ✅ Real-time web dashboard
- ✅ Complete monitoring and analytics
- ✅ All features enabled

---

Made with ❤️ by Lokesh Murali | Paper Trading Mode - Delta Exchange India

