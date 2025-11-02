# AI Trading Agent - Usage Guides

**Comprehensive guides for training, deployment, and usage**

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [BAT Files Guide](#bat-files-guide)
3. [Training Models](#training-models)
4. [Colab Training](#colab-training)
5. [Production Deployment](#production-deployment)
6. [Live Trading Preparation](#live-trading-preparation)

---

## Getting Started

### Prerequisites

**Required Software:**
- Python 3.10+
- Node.js 18+
- Git

**Optional (for Docker):**
- Docker Desktop
- Docker Compose

### Quick Setup

```bash
# 1. Clone repository
git clone <your-repo-url>
cd Trading-Agent

# 2. Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy config\env.example .env
# Edit .env with your API keys

# 5. Start trading bot
start_bot.bat
```

### Configuration

**Essential Settings (`.env`):**
```env
# Delta Exchange API
DELTA_API_KEY=your_api_key
DELTA_API_SECRET=your_api_secret
DELTA_API_URL=https://api.india.delta.exchange

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Trading
INITIAL_BALANCE=10000
TRADING_MODE=paper
```

**Trading Parameters (`config/config.yaml`):**
```yaml
trading:
  symbol: "BTCUSD"
  initial_balance: 10000.0
  timeframes: ["4h"]
  update_interval: 14400  # 4 hours

risk_management:
  max_daily_loss_percent: 5
  max_drawdown_percent: 15
  max_consecutive_losses: 5

position_sizing:
  method: "fixed_fractional"
  risk_per_trade: 0.02  # 2%
```

---

## BAT Files Guide

### Overview

Windows batch scripts for easy system management.

### Available Scripts

#### `start_all.bat` - Launch Everything
**Purpose:** Start bot + API + dashboard in one command

**What it does:**
1. Checks Python and Node.js availability
2. Starts trading bot (minimized window)
3. Starts FastAPI backend (port 8000)
4. Starts Next.js dashboard (port 3000)

**Usage:**
```bash
start_all.bat
```

**Access Points:**
- Dashboard: http://localhost:3000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

---

#### `start_bot.bat` - Trading Bot Only
**Purpose:** Run just the trading bot with Telegram integration

**What it shows:**
- Current configuration
- Model performance stats
- Risk management settings

**Usage:**
```bash
start_bot.bat
```

**Press Ctrl+C to stop gracefully**

---

#### `start_dashboard.bat` - Dashboard Only
**Purpose:** Launch API and dashboard without trading bot

**Useful for:**
- Viewing past trades
- Analyzing performance
- Testing dashboard features
- Manual trading

**Usage:**
```bash
start_dashboard.bat
```

---

#### `check_status.bat` - System Health Check
**Purpose:** Verify all services are running

**Checks:**
- Python processes (bot + API)
- Node.js processes (dashboard)
- Latest log entries
- API health endpoint
- Dashboard accessibility

**Usage:**
```bash
check_status.bat
```

---

#### `restart.bat` - Full System Restart
**Purpose:** Stop everything and restart cleanly

**Process:**
1. Kill all Python/Node processes
2. Wait 5 seconds for cleanup
3. Restart bot, API, dashboard
4. Show latest logs

**Usage:**
```bash
restart.bat
```

---

#### `stop_all.bat` - Stop All Services
**Purpose:** Gracefully stop all running services

**Usage:**
```bash
stop_all.bat
```

---

### Troubleshooting BAT Scripts

**Problem:** Scripts don't start services

**Solution:**
```bash
# Check Python
python --version

# Check Node.js
node --version
npm --version

# Check if in correct directory
dir src\main.py
dir frontend_web\package.json
```

**Problem:** "Python not found" error

**Solution:**
- Install Python 3.10+
- Add to PATH during installation
- Restart terminal

**Problem:** "npm not found" error

**Solution:**
- Install Node.js 18+
- Verify PATH includes npm
- Restart terminal

---

## Training Models

### Overview

Train ML models on historical cryptocurrency data for paper trading.

### Training Process

#### Step 1: Download Historical Data

```bash
# Download data for specific symbol and timeframe
python scripts/download_data.py --symbol BTCUSD --timeframe 4h --days 730

# Options:
# --symbol: BTCUSD
# --timeframe: 15m, 1h, 4h, 1d
# --days: Number of days to fetch (730 = 2 years)
```

#### Step 2: Train Individual Model

```bash
# Train specific model
python scripts/train_model.py --model xgboost --symbol BTCUSD --timeframe 4h

# Available models:
# --model: xgboost, lightgbm, catboost, randomforest, lstm, transformer

# Options:
# --symbol: Trading symbol
# --timeframe: Candle timeframe
# --epochs: Training epochs (for neural networks)
# --test-size: Test split ratio (default: 0.2)
```

#### Step 3: Train All Models

```bash
# Train all models at once
bash scripts/train_all_models.sh

# Or on Windows (if you have Git Bash):
sh scripts/train_all_models.sh

# This will train:
# - XGBoost
# - LightGBM
# - CatBoost
# - Random Forest
# - LSTM (if enabled)
# - Transformer (if enabled)
```

### Production Training

**For best results:**

```bash
# Use production training script
python scripts/train_production_models.py --symbol BTCUSD --timeframe 4h

# This script:
# - Downloads 2 years of data
# - Engineers 40+ features
# - Trains multiple models
# - Validates performance
# - Saves best models
# - Generates performance report
```

**Expected Output:**
```
Training Summary:
Model          Accuracy  Precision  Recall   F1 Score  ROC AUC
RandomForest   95.25%    96.30%     92.59%   94.41%    98.15%
XGBoost        91.67%    89.47%     94.44%   91.89%    96.30%
LightGBM       88.89%    86.96%     90.74%   88.81%    94.82%

Best Model: RandomForest (4/6 criteria)
Models saved to: models/
```

### Model Files

**Location:** `models/`

**Naming Convention:**
```
{model}_{symbol}_{timeframe}_production_{date}.pkl

Examples:
- xgboost_BTCUSD_4h_production_20251014_114541.pkl
- randomforest_BTCUSD_4h_production_20251014_125258.pkl
- lightgbm_BTCUSD_4h_production_20251014_115655.pkl
```

### Validating Models

```bash
# Test model on unseen data
python test_new_models.py

# This will:
# - Load trained models
# - Fetch recent data
# - Generate predictions
# - Show confidence scores
# - Compare to actual prices
```

---

## Colab Training

### Why Google Colab?

- **Free GPU access** - Train models faster
- **No local setup** - Works in browser
- **Collaborative** - Share with team
- **Persistent storage** - Save to Google Drive

### Setup Google Colab

#### Step 1: Upload Files

```python
# In Colab notebook
from google.colab import drive
drive.mount('/content/drive')

# Upload training script
!git clone <your-repo-url>
%cd ai-trading-agent
```

#### Step 2: Install Dependencies

```python
# Install required packages
!pip install -r requirements.txt

# Install additional packages for Colab
!pip install pandas numpy scikit-learn xgboost lightgbm catboost
```

#### Step 3: Run Training Script

```python
# Option 1: Use dedicated Colab script
!python COLAB_COMPLETE_TRAINING_SCRIPT.py

# Option 2: Use production training
!python scripts/train_production_models.py --symbol BTCUSD --timeframe 4h

# Option 3: Train specific model
!python scripts/train_model.py --model xgboost --symbol BTCUSD --timeframe 4h
```

#### Step 4: Save Models to Drive

```python
# Save trained models
import shutil

# Copy to Google Drive
shutil.copytree('models/', '/content/drive/MyDrive/trading_models/')
print("✅ Models saved to Google Drive")
```

#### Step 5: Download Models Locally

1. Navigate to Google Drive
2. Find `/MyDrive/trading_models/`
3. Download `.pkl` files
4. Place in local `models/` directory

### Colab Notebook

**We provide:** `colab_train_models.ipynb`

**Includes:**
- Automated data download
- Feature engineering
- Model training
- Performance evaluation
- Model export

**Usage:**
1. Open in Google Colab
2. Run all cells sequentially
3. Download trained models
4. Use in local trading bot

---

## Production Deployment

### Local Development (Current Setup)

**Already working:**
- Trading bot runs locally
- SQLite database
- In-memory cache
- File-based logging

**To deploy:**
```bash
start_bot.bat  # Windows
python src/main.py  # Linux/Mac
```

### Docker Deployment (Recommended for Production)

#### Step 1: Install Docker

```bash
# Windows/Mac: Install Docker Desktop
# Linux: Install Docker Engine + Docker Compose
```

#### Step 2: Build Images

```bash
# Build all services
docker-compose build

# Or build individually
docker build -t trading-bot .
```

#### Step 3: Configure Environment

```bash
# Copy environment template
cp config/env.example .env

# Edit with production values
nano .env
```

#### Step 4: Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

#### Step 5: Verify Deployment

```bash
# Check API health
curl http://localhost:8000/api/v1/health

# Check dashboard
curl http://localhost:3000

# View metrics
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana
```

### Docker Services

**7 Services Running:**

1. **PostgreSQL + TimescaleDB** - Database (port 5432)
2. **Redis** - Caching layer (port 6379)
3. **RabbitMQ** - Message queue (ports 5672, 15672)
4. **FastAPI** - Backend API (port 8000)
5. **Prometheus** - Metrics collection (port 9090)
6. **Grafana** - Dashboards (port 3000)
7. **Frontend** - Next.js dashboard (port 3001)

### Monitoring

**Prometheus Metrics:**
- http://localhost:9090

**Grafana Dashboards:**
- http://localhost:3000
- Default login: admin/admin

**Available Dashboards:**
1. Trading Overview
2. Model Performance
3. Risk Monitoring
4. System Health

---

## Live Trading Preparation

### ⚠️ IMPORTANT WARNINGS

**DO NOT RUSH TO LIVE TRADING**

This system is designed for paper trading. Live trading requires:
1. Extensive testing (6+ months)
2. Proven profitability
3. Risk capital only (money you can afford to lose)
4. Deep understanding of markets
5. Emotional discipline

### Prerequisites for Live Trading

#### 1. Backtesting Requirements

**Minimum standards:**
- ✅ 2+ years of historical data tested
- ✅ Positive Sharpe ratio (>1.5)
- ✅ Reasonable drawdown (<20%)
- ✅ Consistent monthly returns
- ✅ Win rate >55%
- ✅ Profit factor >2.0

#### 2. Paper Trading Results

**Minimum duration: 6 months**

**Required performance:**
- ✅ Profitable for 6 consecutive months
- ✅ Follows risk management rules
- ✅ No manual intervention needed
- ✅ Stable across market conditions
- ✅ Telegram alerts working correctly

#### 3. Risk Management Verification

**Checklist:**
- ✅ Circuit breakers trigger correctly
- ✅ Position sizing respects limits
- ✅ Stop losses execute properly
- ✅ Daily loss limits enforced
- ✅ Emergency stop functional

#### 4. System Reliability

**Requirements:**
- ✅ 99.9%+ uptime for 1 month
- ✅ No crashes or errors
- ✅ Logs properly recorded
- ✅ Telegram notifications reliable
- ✅ Database backups automated

### Transitioning to Live Trading

**When you're ready (and only when ALL above requirements are met):**

#### Step 1: API Configuration

```env
# Change in .env
TRADING_MODE=live  # ⚠️ USE WITH EXTREME CAUTION

# Use live Delta Exchange credentials
DELTA_API_KEY=<live_key>
DELTA_API_SECRET=<live_secret>
```

#### Step 2: Start with Minimal Capital

```yaml
# config/config.yaml
trading:
  initial_balance: 100.0  # Start VERY small
  
position_sizing:
  risk_per_trade: 0.01  # 1% (very conservative)
  max_position_size: 50  # Small positions

risk_management:
  max_daily_loss_percent: 2  # Strict limit
  max_drawdown_percent: 5    # Very tight
```

#### Step 3: Monitor Intensively

- Check every trade
- Review daily reports
- Monitor Telegram alerts
- Verify risk limits
- Watch for anomalies

#### Step 4: Scale Gradually

**Only if profitable:**
- Month 1: $100
- Month 2: $200 (if +10%)
- Month 3: $500 (if still profitable)
- Month 6: $1,000+ (if consistently profitable)

**Never:**
- Don't add capital after losses
- Don't change strategy mid-month
- Don't disable safety features
- Don't trade on emotions

### Red Flags - Stop Immediately If:

- ❌ Consecutive losing days (>3)
- ❌ Drawdown exceeds 10%
- ❌ Circuit breakers frequently triggered
- ❌ Unexpected trade behavior
- ❌ System errors or crashes
- ❌ Telegram alerts not working
- ❌ Emotional stress affecting decisions

### Final Advice

**Reality Check:**
- Most algo traders lose money initially
- Profitable algo trading is HARD
- Paper trading success ≠ live trading success
- Slippage and fees add up quickly
- Markets change; models need updates
- Emotional discipline is crucial

**Best Practices:**
- Start tiny, scale slowly
- Keep detailed trade journal
- Review performance weekly
- Update models quarterly
- Never risk more than 1-2% per trade
- Have exit strategy BEFORE entering
- Take profits regularly
- Learn from every trade

---

## Support & Resources

### Documentation
- `README.md` - Project overview
- `QUICK_START.md` - Quick start guide  
- `ai_trading_blueprint.md` - Technical architecture
- `DEPLOYMENT_GUIDE.md` - Deployment details
- `DOCUMENTATION.md` - Current status

### Scripts
- All scripts in `scripts/` directory
- BAT files in root directory
- Jupyter notebooks in `notebooks/`

### Community
- GitHub Issues - Bug reports
- Telegram - Trading discussion
- Discord - Development chat

---

**Last Updated:** October 17, 2025  
**Maintained by:** Lokesh Murali  
**License:** Educational Use Only

**Remember: Paper trade until consistently profitable. Your capital is at risk.**

