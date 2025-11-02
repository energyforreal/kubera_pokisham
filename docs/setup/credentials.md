# 🔐 Credentials Setup Guide

## Required Credentials

Your trading agent needs **4 essential credentials** to function:

### 1. ✅ Delta Exchange API Credentials (Required)
### 2. ✅ Telegram Bot Token (Required)
### 3. ✅ Telegram Chat ID (Required)
### 4. ⚙️ Frontend Dashboard URL (Optional)

---

## 📋 Step-by-Step Setup

### Step 1: Create Your Environment File

1. Navigate to the `config/` folder
2. Copy `env.example` to `.env`:
   ```bash
   copy config\env.example .env
   ```
   Or manually create a `.env` file in the project root

---

### Step 2: Get Delta Exchange API Credentials

**What it's for:** Connects to Delta Exchange India for market data and trading

**How to get:**

1. **Sign up/Login** to [Delta Exchange India](https://www.delta.exchange/app/signup)
   
2. **Go to API Settings:**
   - Navigate to: Settings → API Keys
   - Or direct link: https://www.delta.exchange/app/account/api-keys

3. **Create New API Key:**
   - Click "Create New API"
   - **Name:** `Kubera Trading Bot`
   - **Permissions:** 
     - ✅ Read (Required)
     - ✅ Trade (Optional - only if you want live trading later)
     - ❌ Withdraw (Not needed - keep disabled for security)
   
4. **Save Your Credentials:**
   - **API Key** - Copy this
   - **API Secret** - Copy this (shown only once!)
   - **Important:** Save these somewhere safe - you can't see the secret again!

5. **Add to `.env` file:**
   ```env
   DELTA_API_KEY=your_actual_api_key_here
   DELTA_API_SECRET=your_actual_api_secret_here
   DELTA_API_URL=https://api.india.delta.exchange
   ```

---

### Step 3: Create Telegram Bot

**What it's for:** Receive trading alerts and control the bot via Telegram

**How to get:**

1. **Open Telegram** and search for `@BotFather`

2. **Create a new bot:**
   - Send: `/newbot`
   - Choose a name: `Kubera Trading Bot`
   - Choose a username: `kubera_trading_bot` (must end with `bot`)

3. **Save Your Token:**
   - BotFather will give you a token like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`
   - **Copy this token!**

4. **Add to `.env` file:**
   ```env
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   ```

---

### Step 4: Get Your Telegram Chat ID

**What it's for:** The bot needs to know where to send messages

**How to get:**

1. **Start your bot:**
   - In Telegram, find your bot (the username you created)
   - Click **START** or send `/start`

2. **Get your Chat ID:**
   
   **Method 1 - Using a bot (Easiest):**
   - Search for `@userinfobot` in Telegram
   - Start it and it will show your ID
   - Copy the number (e.g., `123456789`)

   **Method 2 - Using web:**
   - Go to: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Replace `<YOUR_BOT_TOKEN>` with your actual bot token
   - Look for `"chat":{"id":123456789}`
   - Copy the number

3. **Add to `.env` file:**
   ```env
   TELEGRAM_CHAT_ID=123456789
   ```

---

### Step 5: (Optional) Setup Frontend Dashboard

If you plan to use the web dashboard:

1. Create `frontend_web/.env.local`:
   ```bash
   copy frontend_web\env.example frontend_web\.env.local
   ```

2. Edit `frontend_web/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

---

## 📝 Complete .env File Template

Your final `.env` file should look like this:

```env
# Delta Exchange API Configuration (India)
DELTA_API_KEY=your_actual_delta_api_key
DELTA_API_SECRET=your_actual_delta_secret
DELTA_API_URL=https://api.india.delta.exchange

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Trading Configuration
INITIAL_BALANCE=10000.0
TRADING_MODE=paper
TRADING_SYMBOL=BTCUSD

# Database
DATABASE_URL=sqlite:///./kubera_pokisham.db

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/kubera_pokisham.log

# Risk Management
MAX_POSITION_SIZE=0.25
RISK_PER_TRADE=0.02
MAX_DAILY_LOSS=0.05
MAX_DRAWDOWN=0.15
MAX_CONSECUTIVE_LOSSES=5
MIN_TIME_BETWEEN_TRADES=300

# Model Configuration
MODEL_PATH=models/xgboost_model.pkl
MIN_CONFIDENCE_THRESHOLD=0.65

# Market Data
UPDATE_INTERVAL=900
TIMEFRAMES=15m,1h,4h
```

---

## ✅ Verification Checklist

Before starting the bot, verify you have:

- [ ] Created `.env` file in project root
- [ ] Added Delta Exchange API Key
- [ ] Added Delta Exchange API Secret
- [ ] Added Telegram Bot Token
- [ ] Added Telegram Chat ID
- [ ] (Optional) Created `frontend_web/.env.local` for dashboard

---

## 🧪 Test Your Setup

### Test 1: Check .env File Exists
```bash
# Windows PowerShell
Test-Path .env
# Should return: True
```

### Test 2: Test Telegram Bot
1. Start the bot: `start_bot.bat`
2. In Telegram, send `/status` to your bot
3. You should get a response!

### Test 3: Check Dashboard (if using)
1. Start all services: `start_all.bat`
2. Open: http://localhost:3000
3. You should see the dashboard!

---

## 🔒 Security Best Practices

### ⚠️ NEVER commit your `.env` file to git!

The `.env` file is already in `.gitignore`, but double-check:

```bash
# Check if .env is ignored
git status
# .env should NOT appear in the list
```

### 🛡️ Keep your credentials safe:
- **Never share** your API keys or bot token
- **Never post** them on public forums/GitHub
- **Use paper trading** first (TRADING_MODE=paper)
- **Start with small amounts** if going live

### 🔐 Delta Exchange Security:
- **Don't enable** withdrawal permissions on API key
- **Use IP whitelist** in Delta Exchange if possible
- **Keep API secret** backed up safely

---

## 🆘 Troubleshooting

### Error: "No .env file found"
**Solution:** Create `.env` file in project root (same folder as `start_bot.bat`)

### Error: "Invalid API credentials"
**Solution:** 
- Check Delta Exchange API key/secret are correct
- Make sure no extra spaces in `.env` file
- Verify API key is active in Delta Exchange

### Error: "Telegram bot not responding"
**Solution:**
- Check bot token is correct
- Make sure you clicked START on the bot in Telegram
- Verify chat ID is correct (should be just numbers)

### Error: "Dashboard can't connect to API"
**Solution:**
- Make sure Backend API is running (`start_all.bat`)
- Check `frontend_web/.env.local` has correct API URL
- Visit http://localhost:8000/docs to verify API is running

---

## 📞 Getting Help

If you need the credentials:
- **Delta Exchange:** https://www.delta.exchange/
- **Telegram BotFather:** Search `@BotFather` in Telegram
- **Chat ID Bot:** Search `@userinfobot` in Telegram

---

## 🎯 Quick Start After Setup

Once credentials are configured:

```bash
# Start everything
start_all.bat

# In Telegram, test with:
/status
/balance
/portfolio
```

Your dashboard will be at: http://localhost:3000

---

**Made with ❤️ for Kubera Pokisham Trading Agent**  
*Paper Trading Mode - Safe Testing Environment*

