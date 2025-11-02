# 🚀 Getting Started - AI Trading Agent

A comprehensive guide to get you up and running quickly with the Kubera Pokisham Trading Agent.

---

## Prerequisites

Before you begin, ensure you have:
- **Python 3.10+** installed
- **Node.js 18+** (for web dashboard)
- **Git** (for cloning repository)
- **Delta Exchange** account with API credentials
- **Telegram** account for bot notifications

---

## Quick Start (3 Options)

### Option 1: Trading Bot Only (Recommended for First Time)

**Best for:** Getting started quickly, testing the system

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure credentials (see setup guide)
copy config\env.example .env
# Edit .env with your API keys

# 3. Start the bot
start_bot.bat
```

**Features:**
- ✅ Paper trading mode (no real money)
- ✅ Multi-model ML predictions
- ✅ Risk management active
- ✅ Telegram notifications
- ✅ Fully functional trading loop

---

### Option 2: Bot + Web Dashboard

**Best for:** Full monitoring experience with visual interface

```bash
# 1. Install all dependencies
pip install -r requirements.txt
cd frontend_web && npm install && cd ..

# 2. Configure credentials
copy config\env.example .env
# Edit .env with your credentials

# 3. Start everything
start_all.bat
```

**Access:**
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Telegram: Your bot in Telegram app

---

### Option 3: Docker Deployment

**Best for:** Production-like environment, isolated deployment

```bash
# 1. Install Docker Desktop

# 2. Configure environment
cp .env.docker.example .env
# Edit with your credentials

# 3. Deploy
docker-compose up -d

# 4. View logs
docker-compose logs -f
```

---

## Step-by-Step First-Time Setup

### Step 1: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install Python packages
pip install -r requirements.txt

# Install frontend (if using dashboard)
cd frontend_web
npm install
cd ..
```

### Step 2: Configure Credentials

See [Credentials Setup Guide](../setup/credentials.md) for detailed instructions.

**Quick version:**
1. Get Delta Exchange API key and secret
2. Create Telegram bot via @BotFather
3. Get your Telegram chat ID
4. Create `.env` file with credentials

**Minimum `.env` file:**
```env
DELTA_API_KEY=your_delta_api_key
DELTA_API_SECRET=your_delta_secret
TELEGRAM_BOT_TOKEN=your_telegram_token
TELEGRAM_CHAT_ID=your_chat_id
TRADING_MODE=paper
```

### Step 3: Verify Installation

```bash
# Test configuration
python test_delta_connection.py

# Should see: ✅ Connection successful
```

### Step 4: Start Trading

```bash
# Option A: Bot only
start_bot.bat

# Option B: Everything
start_all.bat
```

### Step 5: Verify It's Working

**Via Telegram:**
1. Open Telegram
2. Find your bot
3. Send `/status`
4. You should see portfolio information

**Via Dashboard (if started):**
1. Open http://localhost:3000
2. You should see live data loading
3. Check WebSocket connection status (green = connected)

---

## Available Commands (BAT Files)

| Command | Purpose | Use When |
|---------|---------|----------|
| `start_bot.bat` | Trading bot only | You want just the bot with Telegram |
| `start_all.bat` | Bot + API + Dashboard | You want full system with web interface |
| `start_dashboard.bat` | API + Dashboard only | You want to monitor without trading |
| `check_status.bat` | System health check | Verify all services are running |
| `restart.bat` | Full restart | System not responding |
| `stop_all.bat` | Stop everything | End trading session |

---

## Telegram Commands

Once your bot is running, use these commands:

| Command | Description |
|---------|-------------|
| `/status` | Portfolio overview and balance |
| `/positions` | Active trading positions |
| `/signals` | Latest AI predictions |
| `/balance` | Current balance and P&L |
| `/portfolio` | Detailed portfolio breakdown |
| `/pause` | Pause automated trading |
| `/resume` | Resume automated trading |
| `/emergency_stop` | Close all positions immediately |
| `/help` | Show all commands |

---

## Dashboard Features

Access the web dashboard at http://localhost:3000

**Main Features:**
- **Real-time Portfolio** - Live balance, P&L, positions
- **AI Signals** - Current predictions and confidence scores
- **Price Charts** - Real-time cryptocurrency price charts
- **Trade History** - Complete log of all trades
- **Risk Settings** - Adjust risk parameters on-the-fly
- **Position Management** - Edit stop-loss/take-profit
- **Multi-Symbol Support** - Switch between BTC, ETH, SOL, BNB

---

## Troubleshooting

### Bot Won't Start

**Error:** "No .env file found"
```bash
# Solution: Create .env file
copy config\env.example .env
# Then edit .env with your credentials
```

**Error:** "Module not found"
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error:** "Invalid API credentials"
```bash
# Solution: Verify credentials in .env
# - Check for extra spaces
# - Ensure API key is active in Delta Exchange
# - Verify API secret is correct
```

### Dashboard Won't Load

**Error:** "Cannot connect to API"
```bash
# Solution 1: Ensure backend is running
python -m uvicorn backend.api.main:app --reload

# Solution 2: Check ports
# Backend should be on 8000
# Frontend should be on 3000
```

**Error:** "CORS error"
```bash
# Solution: Restart backend
# The backend should automatically handle CORS
```

### Telegram Bot Not Responding

1. Verify bot token is correct in `.env`
2. Ensure you clicked START on the bot
3. Check chat ID is your user ID
4. Restart the bot: `stop_all.bat` then `start_bot.bat`

---

## Next Steps

Once you're up and running:

1. **Monitor for 24 hours** - Let it run and observe behavior
2. **Review logs** - Check `logs/kubera_pokisham.log`
3. **Understand signals** - Learn how AI makes predictions
4. **Adjust risk settings** - Configure to your comfort level
5. **Read full guides** - Explore [Usage Guides](usage-guides.md)

---

## Important Reminders

### ⚠️ Paper Trading Only
- This system is for **testing only**
- No real money is at risk
- Trades are simulated
- Market data is real

### 🛡️ Before Live Trading
**DO NOT enable live trading unless:**
- ✅ You've paper traded for 6+ months
- ✅ You have consistent profitable results
- ✅ You understand all risks
- ✅ You've tested thoroughly
- ✅ You can afford to lose your capital

### 🔒 Security
- **Never commit** `.env` file to git
- **Keep API keys secure**
- **Use paper mode** for testing
- **Enable IP whitelist** in Delta Exchange if possible

---

## Getting Help

### Documentation
- [Full Documentation](documentation.md)
- [Usage Guides](usage-guides.md)
- [BAT Files Guide](bat-files.md)
- [Deployment Guide](../deployment/deployment-guide.md)
- [Architecture Blueprint](../architecture/blueprint.md)

### Support
- Check logs in `logs/kubera_pokisham.log`
- Review error messages carefully
- Verify all prerequisites are met
- Ensure credentials are correct

---

## Quick Reference

### Ports
- **Backend API:** 8000
- **Frontend Dashboard:** 3000
- **Diagnostic Service:** 8080
- **Diagnostic Dashboard:** 3001

### Key Files
- **Configuration:** `config/config.yaml`
- **Environment:** `.env`
- **Logs:** `logs/kubera_pokisham.log`
- **Database:** `kubera_pokisham.db`
- **Models:** `models/*.pkl`

### Access Points
- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:3000
- **Health Check:** http://localhost:8000/api/v1/health
- **Metrics:** http://localhost:9090 (if using Docker)

---

## Summary

1. **Install** dependencies
2. **Configure** credentials in `.env`
3. **Start** with `start_bot.bat` or `start_all.bat`
4. **Verify** via Telegram `/status` or dashboard
5. **Monitor** and learn
6. **Adjust** settings as needed

**You're ready to start!** 🚀

For detailed information on any topic, see the other guides in the [docs/](../README.md) directory.

---

*Last Updated: October 22, 2025*  
*Trading Agent Version: 3.0*

